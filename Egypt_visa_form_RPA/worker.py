"""
Worker process for Egypt Visa RPA: consumes jobs from Redis and runs PDF generation + callback.
Run as a separate process on Railway (same repo, start command: python worker.py).
Requires REDIS_URL. Add Redis to your Railway project and set REDIS_URL (often auto-set by Redis plugin).

Exposes GET /health so Railway's health check passes (same railway.toml as web service).
"""

import json
import logging
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REDIS_QUEUE_KEY = 'egypt_visa_queue'
BLOCK_SECONDS = 30
CALLBACK_TIMEOUT = 60


def send_error_callback(callback_url: str, record_id, error_msg: str):
    """POST error payload to callback_url so Zoho always gets a response (same contract as app)."""
    try:
        payload = {
            'status': 'error',
            'error': error_msg,
            'timestamp': datetime.now().isoformat(),
        }
        if record_id:
            payload['record_id'] = str(record_id).strip()
        r = requests.post(
            callback_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=CALLBACK_TIMEOUT,
        )
        logger.info("Error callback sent to %s -> %s (record_id=%s)", callback_url, r.status_code, record_id)
    except Exception as e:
        logger.error("Failed to send error to callback %s: %s", callback_url, e)


def run_health_server(port: int):
    """Serve GET /health so Railway health check succeeds. Runs in a daemon thread."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health' or self.path == '/health/':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"healthy","service":"Egypt Visa Worker"}')
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, format, *args):
            pass  # quiet
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()


def main():
    redis_url = os.environ.get('REDIS_URL', '').strip()
    if not redis_url:
        logger.error("REDIS_URL is not set. Add Redis to your Railway project and link it.")
        sys.exit(1)

    try:
        import redis
    except ImportError:
        logger.error("redis package not installed. pip install redis")
        sys.exit(1)

    from app import _run_generate_and_callback

    r = redis.from_url(redis_url)
    # Log which Redis we're using (host only, no password) so you can confirm same as web service
    try:
        info = r.info("server")
        logger.info("Connected to Redis (server role=%s)", info.get("redis_mode", "?"))
    except Exception as e:
        logger.warning("Could not get Redis info: %s", e)
    # Start health server so Railway health check (GET /health) passes
    port = int(os.environ.get('PORT', '8080'))
    health_thread = threading.Thread(target=run_health_server, args=(port,), daemon=True)
    health_thread.start()
    logger.info("Worker started. Waiting for jobs on queue %s (block=%ss). Health check on port %s", REDIS_QUEUE_KEY, BLOCK_SECONDS, port)

    while True:
        try:
            # BRPOP: block until a job is available (FIFO: we LPUSH in app, so right side is oldest)
            result = r.brpop(REDIS_QUEUE_KEY, timeout=BLOCK_SECONDS)
            if not result:
                continue
            _key, raw = result
            logger.info("Got job from queue (raw length=%s)", len(raw))
            job = json.loads(raw)
            application_data = job.get('application_data') or {}
            callback_url = (job.get('callback_url') or '').strip()
            record_id = job.get('record_id')
            if not callback_url:
                logger.warning("Job missing callback_url, skipping")
                continue
            logger.info("Processing job record_id=%s callback_url=%s", record_id, callback_url)
            try:
                _run_generate_and_callback(
                    application_data,
                    callback_url,
                    record_id=record_id,
                    redis_client=r,
                )
                logger.info("Job completed for record_id=%s", record_id)
            except Exception as job_err:
                logger.exception("Job failed for record_id=%s: %s", record_id, job_err)
                send_error_callback(callback_url, record_id, str(job_err))
        except redis.ConnectionError as e:
            logger.warning("Redis connection error, retrying: %s", e)
        except json.JSONDecodeError as e:
            logger.error("Invalid job JSON: %s", e)
        except Exception as e:
            logger.exception("Worker loop error: %s", e)


if __name__ == '__main__':
    main()
