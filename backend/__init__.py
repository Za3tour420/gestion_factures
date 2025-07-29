# backend/__init__.py

from flask import Flask
from config import TEMPLATES_DIR, STATIC_DIR
from core.logging_config import setup_logging

import os

def create_app():

    # Setup logging
    setup_logging()

    app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
    app.secret_key = os.urandom(15).hex()
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png', 'webp'}

    from backend.routes import main_routes
    app.register_blueprint(main_routes)
    
    return app
