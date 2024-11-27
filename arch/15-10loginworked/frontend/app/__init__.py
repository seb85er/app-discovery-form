import os
import logging
from flask import Flask
from flask_wtf import CSRFProtect

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(
    __name__, 
    template_folder='../templates',  # Path to the templates folder
    static_folder='../static'        # Path to the static folder
)
app.jinja_env.globals.update(enumerate=enumerate)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your_default_secret_key')

# Enable CSRF protection
csrf = CSRFProtect(app)

logger.debug('Flask app initialized.')

# Import routes AFTER initializing the app
from app import routes
from app import importexport
