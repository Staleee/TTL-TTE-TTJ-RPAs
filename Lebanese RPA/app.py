#!/usr/bin/env python3
"""
Visa Form Webhook Server

A Flask webhook server that:
1. Receives applicant JSON data via POST request
2. Generates a filled visa application form PDF
3. Sends the PDF to an external API along with the applicant name

Usage:
    python app.py

    # Then send POST requests to http://localhost:5000/webhook
"""

import os
import logging
from flask import Flask, request, jsonify, Response
import requests

from config import (
    SERVER_HOST,
    SERVER_PORT,
    DEBUG_MODE,
    POST_API_URL,
    POST_API_KEY,
    POST_API_TIMEOUT,
    PDF_TEMPLATE_PATH,
)
from fill_visa_form import generate_filled_pdf_bytes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


def validate_applicant_data(data: dict) -> tuple:
    """
    Validate the incoming applicant data.
    Returns (is_valid, error_message)
    """
    required_sections = ["personal_info"]
    
    for section in required_sections:
        if section not in data:
            return False, f"Missing required section: {section}"
    
    personal = data.get("personal_info", {})
    required_fields = ["last_name", "first_name"]
    
    for field in required_fields:
        if field not in personal or not personal[field]:
            return False, f"Missing required field: personal_info.{field}"
    
    return True, None


def send_to_external_api(pdf_bytes: bytes, full_name: str) -> dict:
    """
    Send the generated PDF to the external API.
    
    Args:
        pdf_bytes: The filled PDF as bytes
        full_name: The applicant's full name
    
    Returns:
        Response from the external API
    """
    # Prepare the multipart form data
    files = {
        'document': ('visa_form.pdf', pdf_bytes, 'application/pdf')
    }
    data = {
        'name': full_name
    }
    
    # Prepare headers
    headers = {}
    if POST_API_KEY:
        headers['Authorization'] = f'Bearer {POST_API_KEY}'
    
    logger.info(f"Sending document for '{full_name}' to {POST_API_URL}")
    
    try:
        response = requests.post(
            POST_API_URL,
            files=files,
            data=data,
            headers=headers,
            timeout=POST_API_TIMEOUT
        )
        response.raise_for_status()
        
        logger.info(f"Successfully sent document. Status: {response.status_code}")
        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.content else None
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send document: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "visa-form-generator"
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint to receive applicant data and generate visa form.
    
    Expected JSON body: Same structure as visa_applicant_data.json
    
    Returns:
        JSON response with success/error status
    """
    try:
        # Parse incoming JSON
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        logger.info("Received webhook request")
        
        # Validate data
        is_valid, error_msg = validate_applicant_data(data)
        if not is_valid:
            logger.warning(f"Validation failed: {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg
            }), 400
        
        # Check if template exists
        if not os.path.exists(PDF_TEMPLATE_PATH):
            logger.error(f"Template not found: {PDF_TEMPLATE_PATH}")
            return jsonify({
                "success": False,
                "error": "PDF template not found"
            }), 500
        
        # Generate the filled PDF
        logger.info("Generating filled PDF...")
        pdf_bytes, full_name = generate_filled_pdf_bytes(data, PDF_TEMPLATE_PATH)
        logger.info(f"PDF generated for: {full_name}")
        
        # Send to external API
        api_result = send_to_external_api(pdf_bytes, full_name)
        
        if api_result["success"]:
            return jsonify({
                "success": True,
                "message": "Document generated and sent successfully",
                "applicant_name": full_name,
                "external_api_response": api_result.get("response")
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Document generated but failed to send to external API",
                "applicant_name": full_name,
                "error": api_result.get("error")
            }), 502
            
    except Exception as e:
        logger.exception("Error processing webhook request")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/generate', methods=['POST'])
def generate_only():
    """
    Generate PDF without sending to external API.
    Returns the PDF file directly.
    
    Useful for testing or when you want to handle the PDF yourself.
    """
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        
        # Validate data
        is_valid, error_msg = validate_applicant_data(data)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": error_msg
            }), 400
        
        # Generate the filled PDF
        pdf_bytes, full_name = generate_filled_pdf_bytes(data, PDF_TEMPLATE_PATH)
        
        # Return PDF as file download
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=visa_form_{full_name.replace(" ", "_")}.pdf'
            }
        )
        
    except Exception as e:
        logger.exception("Error generating PDF")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    logger.info(f"Starting Visa Form Webhook Server on {SERVER_HOST}:{SERVER_PORT}")
    logger.info(f"POST API URL: {POST_API_URL}")
    logger.info(f"PDF Template: {PDF_TEMPLATE_PATH}")
    
    app.run(
        host=SERVER_HOST,
        port=SERVER_PORT,
        debug=DEBUG_MODE
    )

