# __init__.py
import os
import logging
from flask import Flask, session
from flask_wtf import CSRFProtect

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(
    __name__,
    template_folder='../templates',
    static_folder='../static'
)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your_default_secret_key')
csrf = CSRFProtect(app)

# Define login-related functions directly or import from `auth`
def is_logged_in():
    """Check if the user is logged in."""
    return "username" in session

def get_logged_in_user():
    """Get the username of the currently logged-in user."""
    return session.get("username", "Guest")

# Register Jinja template globals
app.jinja_env.globals.update(is_logged_in=is_logged_in, get_logged_in_user=get_logged_in_user)

logger.debug("Flask app initialized with CSRF protection and template globals.")

# Debugging Imports
try:
    logger.debug("Attempting to import routes...")
    from app import routes
    logger.debug("Successfully imported routes.")
except Exception as e:
    logger.error(f"Failed to import routes: {e}")

try:
    logger.debug("Attempting to import importexport...")
    from app import importexport
    logger.debug("Successfully imported importexport.")
except Exception as e:
    logger.error(f"Failed to import importexport: {e}")

try:
    logger.debug("Attempting to import auth...")
    from app import auth
    logger.debug("Successfully imported auth.")
except Exception as e:
    logger.error(f"Failed to import auth: {e}")

# Print all registered routes
logger.debug("Registered routes:")
for rule in app.url_map.iter_rules():
    logger.debug(f"Endpoint: {rule.endpoint}, Route: {rule}")
