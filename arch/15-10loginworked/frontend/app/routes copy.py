# routes.py
import os
from azure.cosmos import CosmosClient, exceptions
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from app import app  # Import the app instance from app/__init__.py
from app.forms import AppDiscoveryForm #imports classes from forms.py
from app.database import container  # Import database client from database.py
from app.auth import role_required, login_user, logout_user #import auth.py
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, BooleanField, IntegerField, FieldList, FormField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

logger = logging.getLogger(__name__)
logger.debug('Routes are being registered.')
# Get Cosmos DB configuration from environment variables
COSMOS_URI = os.getenv('COSMOS_URI')
COSMOS_KEY = os.getenv('COSMOS_KEY')
COSMOS_DB_NAME = os.getenv('COSMOS_DB_NAME')
COSMOS_CONTAINER_NAME = os.getenv('COSMOS_CONTAINER_NAME')
COSMOS_ENDPOINT = os.getenv('COSMOS_URI')

# Initialize Cosmos client
client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)
database = client.get_database_client(COSMOS_DB_NAME)
container = database.get_container_client(COSMOS_CONTAINER_NAME)


@app.route("/admin")
@role_required("admin")
def admin_dashboard():
    return "Welcome to the Admin Dashboard"

from flask import Flask, request, render_template, redirect, url_for, flash
from app.auth import login_user

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if login_user(username, password):
            return redirect(url_for('home'))  # Adjust this to your desired redirect route
        else:
            flash("Invalid username or password.", "error")
    return render_template('login.html')


@app.route('/')
def home():
    return render_template('home.html') 


@app.route('/add-application', methods=['GET', 'POST'])
#@role_required('admin') 
def add_application():
    form = AppDiscoveryForm()
    logger.debug('Add application page accessed')

    if request.method == 'POST':
        logger.debug(f'Form POST request received with data: {form.data}')
        
        if form.validate_on_submit():
            logger.debug("Form validation passed.")
            
            # Log each section of the form for better visibility
            logger.debug(f"Application Overview Data: {form.app_overview.data}")
            logger.debug(f"Application Stakeholders: {form.app_stakeholders.data}")
            logger.debug(f"Bus Cap Model: {form.app_bus_cap_model.data}")
            logger.debug(f"Operation Data: {form.app_operation.data}")
            logger.debug(f"Server Information: {form.server_information.data}")
            logger.debug(f"Interfaces: {form.interfaces.data}")
            logger.debug(f"Web Systems: {form.web_system.data}")  # Multiple web systems now supported
            logger.debug(f"Databases: {form.database.data}")  # Multiple databases now supported
            logger.debug(f"Performance: {form.performance.data}")

            application_data = {
                "id": form.app_overview.app_name.data,
                "app_name": form.app_overview.app_name.data,
                "app_overview": {
                    "app_name": form.app_overview.app_name.data,
                    "app_desc_full": form.app_overview.app_desc_full.data,
                    "app_desc_one_liner": form.app_overview.app_desc_one_liner.data,
                    "app_type": form.app_overview.app_type.data,
                    "app_age": form.app_overview.app_age.data,
                    "app_version": form.app_overview.app_version.data,
                    "app_runtime_lang": form.app_overview.app_runtime_lang.data,
                    "app_complexity": form.app_overview.app_complexity.data,
                    "app_support": form.app_overview.app_support.data,
                    "app_env": form.app_overview.app_env.data,
                    "app_exists": form.app_overview.app_exists.data,
                    "other_runtime_lang": form.app_overview.other_runtime_lang.data,
                    "business_details": {
                        "business_owner": form.app_overview.business_details.business_owner.data,
                        "business_purpose": form.app_overview.business_details.business_purpose.data,
                        "business_criticality": form.app_overview.business_details.business_criticality.data,
                        "business_impact": form.app_overview.business_details.business_impact.data,
                    },
                    "application_meta": {
                        "number_of_users": form.app_overview.application_meta.number_of_users.data,
                        "release_freq": form.app_overview.application_meta.release_freq.data,
                        "work_hours_stand": form.app_overview.application_meta.work_hours_stand.data,
                        "planned_reg_downtime": form.app_overview.application_meta.planned_reg_downtime.data,
                        "documentation": form.app_overview.application_meta.documentation.data,
                    }
                },
                "app_stakeholders": [stakeholder.data for stakeholder in form.app_stakeholders],
                "app_bus_cap_model": form.app_bus_cap_model.data,
                "app_operation": form.app_operation.data,
                "server_information": [server.data for server in form.server_information],
                "interfaces": [interface.data for interface in form.interfaces],
                "web_system": [web_system.data for web_system in form.web_system],  # Multiple web systems supported
                "database": [database.data for database in form.database],  # Multiple databases supported
                "performance": form.performance.data
            }

            logger.debug(f'Application data to be saved: {application_data}')
            
            try:
                # Create item in Cosmos DB
                container.create_item(body=application_data)
                logger.info(f'Application {form.app_overview.app_name.data} added successfully to Cosmos DB')
                return redirect(url_for('view_applications'))
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Error inserting data into Cosmos DB: {e}")
        else:
            logger.warning('Form validation failed')
            logger.debug(f'Form errors: {form.errors}')

    return render_template('add_application.html', form=form)


# Route for viewing existing applications
@app.route('/view-applications', methods=['GET'])
#@role_required('test')
def view_applications():
    form = AppDiscoveryForm()
    try:
        applications = list(container.read_all_items())
        for app in applications:
            app['completion_percentage'], app['missing_fields'] = calculate_completion(app)
        logger.info(f"Fetched {len(applications)} applications from Cosmos DB")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error fetching data from Cosmos DB: {e}")
        applications = []
    
    return render_template('view_applications.html', applications=applications, form=form)

# Helper function to calculate completion percentage of an application
def calculate_completion(application_data):
    total_fields = 0
    filled_fields = 0
    missing_fields = []

    def check_field(field, field_name):
        nonlocal total_fields, filled_fields
        total_fields += 1
        if field and (not isinstance(field, str) or field.strip()):
            filled_fields += 1
        else:
            missing_fields.append(field_name)

    app_overview = application_data.get("app_overview", {})
    for field_name, field_value in app_overview.items():
        check_field(field_value, field_name)

    for stakeholder in application_data.get("app_stakeholders", []):
        for field_name, field_value in stakeholder.items():
            check_field(field_value, f"stakeholder {field_name}")

    for server in application_data.get("server_information", []):
        for field_name, field_value in server.items():
            check_field(field_value, f"server {field_name}")

    if total_fields > 0:
        completion_percentage = (filled_fields / total_fields) * 100
    else:
        completion_percentage = 0

    return int(completion_percentage), missing_fields

@app.route('/remove-application/<app_name>', methods=['POST'])
def remove_application(app_name):
    logger.debug(f'Remove application page accessed for {app_name}')
    try:
        container.delete_item(item=app_name, partition_key=app_name)
        logger.info(f"Application {app_name} removed successfully from Cosmos DB")
        return redirect(url_for('view_applications'))
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error removing data from Cosmos DB: {e}")
        return f"An error occurred while deleting {app_name}."

@app.route('/edit-application/<app_name>', methods=['GET', 'POST'])
def edit_application(app_name):
    try:
        # Fetch the existing application data from Cosmos DB
        app_item = container.read_item(item=app_name, partition_key=app_name)
        logger.debug(f"Fetched application {app_name} from Cosmos DB: {app_item}")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error fetching data for {app_name}: {e}")
        flash(f"Application {app_name} could not be found.", "error")
        return redirect(url_for('view_applications'))

    # Populate the form with existing data
    form = AppDiscoveryForm(data=app_item)

    if request.method == 'POST':
        logger.debug(f'Edit Form POST request received with data: {form.data}')
        
        if form.validate_on_submit():
            logger.debug("Form validation passed.")
            
            # Log each section of the form for better visibility
            logger.debug(f"Application Overview Data: {form.app_overview.data}")
            logger.debug(f"Application Stakeholders: {form.app_stakeholders.data}")
            logger.debug(f"Bus Cap Model: {form.app_bus_cap_model.data}")
            logger.debug(f"Operation Data: {form.app_operation.data}")
            logger.debug(f"Server Information: {form.server_information.data}")
            logger.debug(f"Interfaces: {form.interfaces.data}")
            logger.debug(f"Web Systems: {form.web_system.data}")
            logger.debug(f"Databases: {form.database.data}")
            logger.debug(f"Performance: {form.performance.data}")

            # Create updated application data based on form input
            updated_application_data = {
                "id": form.app_overview.app_name.data,
                "app_name": form.app_overview.app_name.data,
                "app_overview": {
                    "app_name": form.app_overview.app_name.data,
                    "app_desc_full": form.app_overview.app_desc_full.data,
                    "app_desc_one_liner": form.app_overview.app_desc_one_liner.data,
                    "app_type": form.app_overview.app_type.data,
                    "app_age": form.app_overview.app_age.data,
                    "app_version": form.app_overview.app_version.data,
                    "app_runtime_lang": form.app_overview.app_runtime_lang.data,
                    "app_complexity": form.app_overview.app_complexity.data,
                    "app_support": form.app_overview.app_support.data,
                    "app_env": form.app_overview.app_env.data,
                    "app_exists": form.app_overview.app_exists.data,
                    "other_runtime_lang": form.app_overview.other_runtime_lang.data,
                    "business_details": {
                        "business_owner": form.app_overview.business_details.business_owner.data,
                        "business_purpose": form.app_overview.business_details.business_purpose.data,
                        "business_criticality": form.app_overview.business_details.business_criticality.data,
                        "business_impact": form.app_overview.business_details.business_impact.data,
                    },
                    "application_meta": {
                        "number_of_users": form.app_overview.application_meta.number_of_users.data,
                        "release_freq": form.app_overview.application_meta.release_freq.data,
                        "work_hours_stand": form.app_overview.application_meta.work_hours_stand.data,
                        "planned_reg_downtime": form.app_overview.application_meta.planned_reg_downtime.data,
                        "documentation": form.app_overview.application_meta.documentation.data,
                    }
                },
                "app_stakeholders": [stakeholder.data for stakeholder in form.app_stakeholders],
                "app_bus_cap_model": form.app_bus_cap_model.data,
                "app_operation": form.app_operation.data,
                "server_information": [server.data for server in form.server_information],
                "interfaces": [interface.data for interface in form.interfaces],
                "web_system": [web_system.data for web_system in form.web_system],  # Handles multiple web systems
                "database": [database.data for database in form.database],  # Handles multiple databases
                "performance": form.performance.data
            }

            logger.debug(f'Updated application data to be saved: {updated_application_data}')
            
            try:
                # Replace the item in Cosmos DB with the updated data
                container.replace_item(item=app_name, body=updated_application_data)
                logger.info(f"Application {app_name} updated successfully.")
                flash(f"Application {app_name} updated successfully!", "success")
                return redirect(url_for('view_applications'))
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Error updating application: {e}")
                flash(f"Error updating application {app_name}: {e}", "error")

    return render_template('add_application.html', form=form, edit_mode=True, app_name=app_name)
