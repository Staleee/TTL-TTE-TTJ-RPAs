"""
Configuration settings for the Visa Form Webhook Server

Set these as environment variables in Railway/Render:
- POST_API_URL: Your external API endpoint
- POST_API_KEY: API key for authentication (optional)
"""
import os

# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = int(os.environ.get("PORT", 5000))
DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"

# External API settings (where PDF gets sent)
POST_API_URL = os.environ.get("POST_API_URL", "https://your-api-endpoint.com/upload")
POST_API_KEY = os.environ.get("POST_API_KEY", "")
POST_API_TIMEOUT = int(os.environ.get("POST_API_TIMEOUT", 30))

# PDF template path
PDF_TEMPLATE_PATH = os.environ.get("PDF_TEMPLATE_PATH", "Visa_Application_Form.pdf")

