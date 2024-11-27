import os
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.csrf import CSRFError
from wtforms import StringField, BooleanField, IntegerField, FieldList, FormField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional
from werkzeug.utils import secure_filename
from azure.cosmos import CosmosClient, exceptions

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your_default_secret_key')

# Enable CSRF protection
csrf = CSRFProtect(app)

logger.debug('Flask app initialized.')

from app import app 
from app.database import container

if __name__ == '__main__':
    app.run(debug=True)
