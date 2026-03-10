"""
ASGI entry point for uvicorn: uvicorn api_server:app

Exposes the same Flask app (from app.py) as ASGI so it runs under uvicorn.
"""
from app import app as flask_app
from asgiref.wsgi import WsgiToAsgi

app = WsgiToAsgi(flask_app)
