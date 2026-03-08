"""
Worker process for Egypt Visa RPA: consumes jobs from Redis and runs PDF generation + callback.
Run as a separate process on Railway (same repo, start command: python worker.py).
Requires REDIS_URL. Add Redis to your Railway project and set REDIS_URL (often auto-set by Redis plugin).
"""

import json
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REDIS_QUEUE_KEY = 'egypt_visa_queue'
BLOCK_SECONDS = 30


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
    logger.info("Worker started. Waiting for jobs on queue %s (block=%ss)", REDIS_QUEUE_KEY, BLOCK_SECONDS)

    while True:
        try:
            # BRPOP: block until a job is available (FIFO: we LPUSH in app, so right side is oldest)
            result = r.brpop(REDIS_QUEUE_KEY, timeout=BLOCK_SECONDS)
            if not result:
                continue
            _key, raw = result
            job = json.loads(raw)
            application_data = job.get('application_data') or {}
            callback_url = (job.get('callback_url') or '').strip()
            record_id = job.get('record_id')
            if not callback_url:
                logger.warning("Job missing callback_url, skipping")
                continue
            logger.info("Processing job record_id=%s -> %s", record_id, callback_url)
            _run_generate_and_callback(
                application_data,
                callback_url,
                record_id=record_id,
                redis_client=r,
            )
        except redis.ConnectionError as e:
            logger.warning("Redis connection error, retrying: %s", e)
        except json.JSONDecodeError as e:
            logger.error("Invalid job JSON: %s", e)
        except Exception as e:
            logger.exception("Worker job failed: %s", e)


if __name__ == '__main__':
    main()
