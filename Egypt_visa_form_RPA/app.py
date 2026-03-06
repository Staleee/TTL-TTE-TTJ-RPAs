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


# Meta keys we strip from the request body (not part of visa application data)
META_KEYS = frozenset({'callback_url', 'record_id'})


def _run_generate_and_callback(application_data: dict, callback_url: str, record_id: str = None):
    """Background: generate PDF then POST to callback_url with PDF + record_id (for Zoho to attach to record)."""
    try:
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
            # POST PDF to Zoho's receive API: document + record_id so they can upload to that record
            files = {'document': (filename, pdf_data, 'application/pdf')}
            data = {
                'status': 'success',
                'applicant_name': f"{app_obj.first_name} {app_obj.family_name}",
            }
            if record_id is not None and str(record_id).strip():
                data['record_id'] = str(record_id).strip()
            r = requests.post(callback_url, files=files, data=data, timeout=CALLBACK_TIMEOUT)
            logger.info(f"Callback to {callback_url} (record_id={record_id}) -> {r.status_code}")
        finally:
            try:
                automation.quit()
            except Exception:
                pass
    except Exception as e:
        logger.exception("Background PDF generation failed")
        try:
            payload = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
            }
            if record_id is not None and str(record_id).strip():
                payload['record_id'] = str(record_id).strip()
            requests.post(
                callback_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=CALLBACK_TIMEOUT
            )
        except Exception as cb_err:
            logger.error(f"Failed to send error to callback: {cb_err}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'service': 'Egypt Visa Form RPA',
        'timestamp': datetime.now().isoformat()
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

        # Async: return 202 and process in background, then POST PDF + record_id to callback_url
        if callback_url:
            logger.info(f"Async mode: will callback to {callback_url} with record_id={record_id}")
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
            'POST /generate-visa-pdf': 'Generate visa PDF from JSON data',
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

