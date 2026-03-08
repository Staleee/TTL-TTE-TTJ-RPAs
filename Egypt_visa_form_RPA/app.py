"""
Flask web server for Egypt Visa Form RPA
Accepts webhook POST requests with JSON data and returns PDF.
Supports callback_url for async (avoids Zoho/timeout issues).
"""

from flask import Flask, request, jsonify, send_file
from pathlib import Path
import json
import logging
import io
import os
import traceback
import threading
from datetime import datetime
import requests

from form_automation import EgyptVisaFormAutomation, VisaFormFiller
from data_models import VisaApplication
from pdf_generator import create_pdf_from_filled_form

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CALLBACK_TIMEOUT = 60
REDIS_QUEUE_KEY = 'egypt_visa_queue'
REDIS_STATUS_PREFIX = 'egypt_visa:status:'
JOB_STATUS_TTL = 86400  # 24h

# In-memory job status (keyed by record_id) so you can poll when callback was triggered. Lost on restart.
_job_status = {}
_job_status_lock = threading.Lock()

# Meta keys we strip from the request body (not part of visa application data)
META_KEYS = frozenset({'callback_url', 'record_id'})


def _set_job_status(record_id: str, data: dict, redis_client=None):
    """Update in-memory job status and optionally Redis (for worker process)."""
    with _job_status_lock:
        _job_status[record_id] = data
    if redis_client and record_id:
        try:
            redis_client.set(REDIS_STATUS_PREFIX + record_id, json.dumps(data), ex=JOB_STATUS_TTL)
        except Exception as e:
            logger.warning(f"Failed to write job status to Redis: {e}")


def _run_generate_and_callback(application_data: dict, callback_url: str, record_id: str = None, redis_client=None):
    """Background: generate PDF then POST to callback_url with PDF + record_id (for Zoho to attach to record)."""
    rid = (record_id and str(record_id).strip()) or None
    logger.info(f"[record_id={rid}] JOB STARTED - will callback to {callback_url}")
    if rid:
        _set_job_status(rid, {'status': 'processing', 'started_at': datetime.now().isoformat(), 'callback_sent': False}, redis_client)

    try:
        logger.info(f"[record_id={rid}] Starting PDF generation...")
        app_obj = VisaApplication(application_data)
        config_path = Path('config/config.json')
        automation = EgyptVisaFormAutomation(config_path)
        try:
            automation.setup_driver()
            automation.navigate_to_form()
            filler = VisaFormFiller(automation)
            filler.fill_complete_form(app_obj)
            pdf_path = create_pdf_from_filled_form(automation, app_obj, click_create_button=True)
            if not pdf_path or not pdf_path.exists():
                raise Exception("PDF generation failed - file not created")
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            pdf_path.unlink()
            filename = app_obj.get_output_filename()
            logger.info(f"[record_id={rid}] PDF ready ({len(pdf_data)} bytes), triggering callback to {callback_url}...")
            # POST PDF to Zoho's receive API: document + record_id so they can upload to that record
            files = {'document': (filename, pdf_data, 'application/pdf')}
            data = {
                'status': 'success',
                'applicant_name': f"{app_obj.first_name} {app_obj.family_name}",
            }
            if rid:
                data['record_id'] = rid
            r = requests.post(callback_url, files=files, data=data, timeout=CALLBACK_TIMEOUT)
            logger.info(f"[record_id={rid}] Callback TRIGGERED -> {callback_url} returned status {r.status_code}")
            if rid:
                _set_job_status(rid, {
                    'status': 'done',
                    'callback_sent': True,
                    'callback_status_code': r.status_code,
                    'finished_at': datetime.now().isoformat(),
                }, redis_client)
        finally:
            try:
                automation.quit()
            except Exception:
                pass
    except Exception as e:
        logger.exception(f"[record_id={rid}] PDF generation failed: {e}")
        if rid:
            _set_job_status(rid, {
                'status': 'failed',
                'error': str(e),
                'finished_at': datetime.now().isoformat(),
                'callback_sent': False,
            }, redis_client)
        try:
            payload = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
            if rid:
                payload['record_id'] = rid
            logger.info(f"[record_id={rid}] Sending error to callback URL...")
            r = requests.post(
                callback_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=CALLBACK_TIMEOUT
            )
            logger.info(f"[record_id={rid}] Error callback TRIGGERED -> {callback_url} returned status {r.status_code}")
            if rid:
                with _job_status_lock:
                    _job_status[rid]['callback_sent'] = True
                    _job_status[rid]['callback_status_code'] = r.status_code
                _set_job_status(rid, _job_status[rid], redis_client)
        except Exception as cb_err:
            logger.error(f"[record_id={rid}] Failed to send error to callback: {cb_err}")
            if rid:
                with _job_status_lock:
                    _job_status[rid]['callback_sent'] = False
                    _job_status[rid]['callback_error'] = str(cb_err)
                _set_job_status(rid, _job_status[rid], redis_client)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'service': 'Egypt Visa Form RPA',
        'timestamp': datetime.now().isoformat()
    }), 200


def _get_redis():
    """Return Redis client if REDIS_URL is set, else None. Cached per request to avoid reconnecting every time."""
    url = os.environ.get('REDIS_URL', '').strip()
    if not url:
        return None
    try:
        import redis
        return redis.from_url(url)
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        return None


@app.route('/job-status', methods=['GET'])
def job_status():
    """
    Poll this to see when the callback was triggered for a given record_id.
    Only works when you sent record_id in the trigger request.
    When Redis is used, status is read from Redis (worker updates it).
    """
    record_id = (request.args.get('record_id') or '').strip()
    if not record_id:
        return jsonify({'error': 'Missing query param: record_id'}), 400
    # If Redis is configured, worker writes status there; web app reads it
    r = _get_redis()
    if r:
        try:
            raw = r.get(REDIS_STATUS_PREFIX + record_id)
            if raw:
                info = json.loads(raw)
                return jsonify({'record_id': record_id, **info}), 200
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
    with _job_status_lock:
        info = _job_status.get(record_id)
    if info is None:
        return jsonify({
            'record_id': record_id,
            'status': 'unknown',
            'message': 'No job found for this record_id (maybe not started yet, or server restarted)'
        }), 200
    return jsonify({
        'record_id': record_id,
        **info,
    }), 200


@app.route('/generate-visa-pdf', methods=['POST'])
def generate_visa_pdf():
    """
    Webhook endpoint to generate visa PDF from JSON data.
    
    If body includes "callback_url", returns 202 immediately and POSTs the PDF
    (or error) to that URL when done (avoids client timeouts e.g. Zoho).
    Otherwise returns the PDF synchronously.
    """
    try:
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'timestamp': datetime.now().isoformat()
            }), 400

        raw = request.get_json()
        callback_url = (raw.get('callback_url') or '').strip()
        record_id = raw.get('record_id')  # Zoho record ID – we send it back in callback so Zoho can attach PDF
        application_data = {k: v for k, v in raw.items() if k not in META_KEYS}

        try:
            app_obj = VisaApplication(application_data)
            is_valid, errors = app_obj.validate()
            if not is_valid:
                logger.error(f"Validation failed: {errors}")
                return jsonify({
                    'error': 'Validation failed',
                    'details': errors,
                    'timestamp': datetime.now().isoformat()
                }), 400
        except Exception as e:
            logger.error(f"Error parsing application data: {e}")
            return jsonify({
                'error': 'Invalid application data format',
                'details': str(e),
                'timestamp': datetime.now().isoformat()
            }), 400

        # Async: return 202 and process via Redis worker (or in-process thread if no Redis)
        if callback_url:
            redis_url = os.environ.get('REDIS_URL', '').strip()
            if redis_url:
                # Push job to Redis; worker process will run PDF + callback
                try:
                    import redis
                    r = redis.from_url(redis_url)
                    job = {
                        'application_data': application_data,
                        'callback_url': callback_url,
                        'record_id': record_id,
                    }
                    r.lpush(REDIS_QUEUE_KEY, json.dumps(job))
                    if record_id:
                        rid = str(record_id).strip()
                        r.set(REDIS_STATUS_PREFIX + rid, json.dumps({
                            'status': 'queued',
                            'started_at': datetime.now().isoformat(),
                            'callback_sent': False,
                        }), ex=JOB_STATUS_TTL)
                    logger.info(f"Enqueued job for record_id={record_id}, callback to {callback_url}")
                except Exception as e:
                    logger.exception(f"Failed to enqueue job: {e}")
                    return jsonify({
                        'error': 'Queue unavailable',
                        'details': str(e),
                        'timestamp': datetime.now().isoformat()
                    }), 503
                return jsonify({
                    'status': 'accepted',
                    'message': 'Job queued. Worker will generate PDF and POST to callback_url when done.',
                    'callback_url': callback_url,
                    'record_id': record_id,
                    'timestamp': datetime.now().isoformat()
                }), 202
            # No Redis: run in background thread (may not complete on Railway after 202)
            logger.info(f"Async mode (thread): will callback to {callback_url} with record_id={record_id}")
            thread = threading.Thread(
                target=_run_generate_and_callback,
                args=(application_data, callback_url),
                kwargs={'record_id': record_id},
                daemon=True
            )
            thread.start()
            return jsonify({
                'status': 'accepted',
                'message': 'Processing in background. PDF and record_id will be POSTed to callback_url when done.',
                'callback_url': callback_url,
                'record_id': record_id,
                'timestamp': datetime.now().isoformat()
            }), 202

        # Synchronous: generate and return PDF
        logger.info(f"Sync mode: generating PDF for {app_obj.first_name} {app_obj.family_name}")
        config_path = Path('config/config.json')
        automation = EgyptVisaFormAutomation(config_path)
        try:
            automation.setup_driver()
            automation.navigate_to_form()
            filler = VisaFormFiller(automation)
            filler.fill_complete_form(app_obj)
            pdf_path = create_pdf_from_filled_form(automation, app_obj, click_create_button=True)
            if not pdf_path or not pdf_path.exists():
                raise Exception("PDF generation failed - file not created")
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            pdf_path.unlink()
            filename = app_obj.get_output_filename()
            return send_file(
                io.BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        finally:
            try:
                automation.quit()
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'PDF generation failed',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API documentation"""
    return jsonify({
        'service': 'Egypt Visa Form RPA API',
        'version': '1.0',
        'endpoints': {
            'POST /generate-visa-pdf': 'Generate visa PDF (sync or async with callback_url + record_id)',
            'GET /job-status?record_id=xxx': 'Poll to see when callback was triggered for that record_id',
            'GET /health': 'Health check endpoint',
            'GET /': 'This documentation'
        },
        'usage': {
            'method': 'POST',
            'url': '/generate-visa-pdf',
            'headers': {'Content-Type': 'application/json'},
            'body': 'Visa JSON + optional callback_url + record_id. We POST PDF + record_id to callback_url when done. See API_REQUEST_BODY.md.',
            'response': 'PDF, or 202 then we POST to your callback_url with document + record_id'
        },
        'example': {
            'curl': 'curl -X POST http://your-app.railway.app/generate-visa-pdf -H "Content-Type: application/json" -d @data/sample_application.json --output visa.pdf'
        }
    }), 200


if __name__ == '__main__':
    # For local testing
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

