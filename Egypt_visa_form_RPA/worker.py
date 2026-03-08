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
CALLBACK_HEADERS = {'User-Agent': 'EgyptVisaRPA/1.0 (Callback)', 'Accept': 'application/json, */*'}


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
        headers = {**CALLBACK_HEADERS, 'Content-Type': 'application/json'}
        r = requests.post(callback_url, json=payload, headers=headers, timeout=CALLBACK_TIMEOUT)
        logger.info("Error callback sent to %s -> %s (record_id=%s)", callback_url, r.status_code, record_id)
        if r.status_code >= 400:
            logger.warning("Error callback response body: %s", (r.text[:500] if r.text else "(empty)"))
    except Exception as e:
        logger.error("Failed to send error to callback %s: %s", callback_url, e)


def run_health_server(port: int):
    """Serve GET /health so Railway health check succeeds. Runs in a daemon thread."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith('/health'):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                body = {"status": "healthy", "service": "Egypt Visa Worker"}
                # So you can verify worker sees Railway vars: GET /health?zoho=1
                if 'zoho=1' in self.path or 'zoho=1' in (self.path.split('?')[-1] if '?' in self.path else ''):
                    body["zoho_access_token_set"] = bool((os.environ.get('ZOHO_ACCESS_TOKEN') or os.environ.get('ZOHO_OAUTH_TOKEN') or '').strip())
                    body["zoho_refresh_token_set"] = bool((os.environ.get('ZOHO_REFRESH_TOKEN') or '').strip())
                    body["zoho_can_refresh"] = bool(
                        (os.environ.get('ZOHO_REFRESH_TOKEN') or '').strip()
                        and (os.environ.get('ZOHO_CLIENT_ID') or '').strip()
                        and (os.environ.get('ZOHO_CLIENT_SECRET') or '').strip()
                    )
                self.wfile.write(json.dumps(body).encode())
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

    # Log whether Zoho env vars are present (so you can confirm worker has them after redeploy)
    has_access = bool((os.environ.get('ZOHO_ACCESS_TOKEN') or '').strip())
    has_refresh = bool((os.environ.get('ZOHO_REFRESH_TOKEN') or '').strip())
    logger.info("ZOHO_ACCESS_TOKEN set: %s | ZOHO_REFRESH_TOKEN set: %s", has_access, has_refresh)

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
            # Process if we have record_id (built-in Zoho upload) or callback_url
            if not record_id and not callback_url:
                logger.warning("Job missing both record_id and callback_url, skipping")
                continue
            logger.info("Processing job record_id=%s callback_url=%s", record_id, callback_url)
            zoho_oauthtoken = job.get('zoho_oauthtoken')
            try:
                _run_generate_and_callback(
                    application_data,
                    callback_url,
                    record_id=record_id,
                    redis_client=r,
                    zoho_oauthtoken=zoho_oauthtoken,
                )
                logger.info("Job completed for record_id=%s", record_id)
            except Exception as job_err:
                logger.exception("Job failed for record_id=%s: %s", record_id, job_err)
                if callback_url:
                    send_error_callback(callback_url, record_id, str(job_err))
        except redis.ConnectionError as e:
            logger.warning("Redis connection error, retrying: %s", e)
        except json.JSONDecodeError as e:
            logger.error("Invalid job JSON: %s", e)
        except Exception as e:
            logger.exception("Worker loop error: %s", e)


if __name__ == '__main__':
    main()
