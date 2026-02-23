"""
Flask web server for Egypt Visa Form RPA
Accepts webhook POST requests with JSON data and returns PDF
"""

from flask import Flask, request, jsonify, send_file
from pathlib import Path
import json
import logging
import io
import traceback
from datetime import datetime

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
    Webhook endpoint to generate visa PDF from JSON data
    
    Request body: JSON with visa application data
    Response: PDF file
    """
    try:
        # Get JSON data from request
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        application_data = request.get_json()
        logger.info(f"Received visa application request for: {application_data.get('personal_info', {}).get('first_name', 'Unknown')}")
        
        # Validate and create VisaApplication object
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
        
        # Initialize automation
        config_path = Path('config/config.json')
        automation = EgyptVisaFormAutomation(config_path)
        
        try:
            # Setup and run automation
            logger.info("Setting up Chrome WebDriver...")
            automation.setup_driver()
            
            logger.info("Navigating to form...")
            automation.navigate_to_form()
            
            logger.info("Filling form...")
            filler = VisaFormFiller(automation)
            filler.fill_complete_form(app_obj)
            
            logger.info("Generating PDF with QR code...")
            pdf_path = create_pdf_from_filled_form(automation, app_obj, click_create_button=True)
            
            if not pdf_path or not pdf_path.exists():
                raise Exception("PDF generation failed - file not created")
            
            logger.info(f"✓ PDF generated successfully: {pdf_path}")
            
            # Read PDF into memory
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            # Clean up PDF file
            pdf_path.unlink()
            
            # Get applicant name for filename
            filename = app_obj.get_output_filename()
            
            logger.info(f"✓ Sending PDF: {filename} ({len(pdf_data)} bytes)")
            
            # Return PDF as response
            return send_file(
                io.BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
        finally:
            # Always close browser
            try:
                automation.quit()
            except:
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
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': 'JSON with visa application data (see data/sample_application.json)',
            'response': 'PDF file (application/pdf)'
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

