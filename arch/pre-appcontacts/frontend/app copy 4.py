import os
import logging
import csv
import pyexcel
import io
from io import BytesIO, StringIO
from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.csrf import CSRFError
from wtforms import StringField, BooleanField, IntegerField, FieldList, FormField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional
from werkzeug.utils import secure_filename
from azure.cosmos import CosmosClient, exceptions

import pandas as pd

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your_default_secret_key')

# Enable CSRF protection
csrf = CSRFProtect(app)

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

# Define Forms
class ApplicationStakeholderForm(FlaskForm):
    stakeholder_name = StringField('Name')
    contact_type = StringField('Contact Type')
    business_unit = StringField('Business Unit')
    department = StringField('Department')
    number = StringField('Phone Number')
    email = StringField('Email')
    position = StringField('Position')

class ApplicationBusCapModelForm(FlaskForm):
    capability_model = StringField('Capability Model')
    front_office = BooleanField('Front Office')
    back_office = BooleanField('Back Office')
    middle_office = BooleanField('Middle Office')
    it_for_it = BooleanField('IT for IT')  
    enterprise = BooleanField('Enterprise')  
    not_mapped = BooleanField('Not Mapped')

class BusinessDetailsForm(FlaskForm):
    business_owner = StringField('Business Owner')
    business_purpose = StringField('Business Purpose')
    business_criticality = IntegerField('Business Criticality', validators=[Optional()])
    business_impact = IntegerField('Business Impact', validators=[Optional()])

class ApplicationMetaForm(FlaskForm):
    number_of_users = IntegerField('Number of Users', validators=[Optional()])
    release_freq = StringField('Release Frequency')
    work_hours_stand = StringField('Work Hours Standard')
    planned_reg_downtime = StringField('Planned Regular Downtime')
    documentation = TextAreaField('Documentation')

class ApplicationOperationForm(FlaskForm):
    high_availability = BooleanField('High Availability')
    disaster_recovery = BooleanField('Disaster Recovery')
    rto = StringField('RTO')
    rpo = StringField('RPO')

class ServerInformationForm(FlaskForm):
    environment = StringField('Environment')
    hostname = StringField('Hostname')
    role = StringField('Role')
    platform_type = StringField('Platform Type')
    shared_or_dedicated = StringField('Shared or Dedicated')
    os = StringField('Operating System')
    os_features = StringField('OS Features')
    cpu = StringField('CPU')
    ram = StringField('RAM')
    os_disk_gb = IntegerField('OS Disk Size (GB)', validators=[Optional()])
    data_disk_count = IntegerField('Data Disk Count', validators=[Optional()])
    shared_data_store = StringField('Shared Data Store')
    
    # Network Information (now part of ServerInformationForm)
    network_environment = StringField('Network Environment')
    network_hostname = StringField('Network Hostname')
    network_name = StringField('Network Name')
    subnet = StringField('Subnet')
    ip_address = StringField('IP Address')

class InterfacesForm(FlaskForm):
    source_app = StringField('Source App')
    target_app = StringField('Target App')
    direction = StringField('Direction')
    frequency = StringField('Frequency')
    mechanism = StringField('Mechanism')
    trigger = StringField('Trigger')
    bandwidth = StringField('Bandwidth')
    protcol = StringField('Protocol')
    other_system_owner = StringField('Other System Owner')

class ApplicationOverviewForm(FlaskForm):
    app_name = StringField('App Name', validators=[DataRequired()])
    app_desc_full = TextAreaField('App Description Full')
    app_desc_one_liner = StringField('App Description One Liner')
    app_type = StringField('App Type')
    app_age = StringField('App Age')
    app_version = StringField('App Version')
    app_runtime_lang = StringField('App Runtime Language')
    app_complexity = StringField('App Complexity')
    app_support = StringField('App Support')
    app_env = StringField('App Environment')
    app_exists = BooleanField('App Exists')
    other_runtime_lang = StringField('Other Runtime Language')
    business_details = FormField(BusinessDetailsForm)
    application_meta = FormField(ApplicationMetaForm)

# New Forms for Web System Information, Database Information, and Performance Indicators
class WebSystemInformationForm(FlaskForm):
    environment = StringField('Environment')
    internet_access = StringField('Internet Access')
    external_access = StringField('External Access')
    web_server = StringField('Web Server')
    public_ips = StringField('Public IPs')
    authentication = StringField('Authentication')
    authorization = StringField('Authorization')
    load_balanced = BooleanField('Load Balanced')
    url = StringField('URL')
    certificate = StringField('Certificate')

class DatabaseInformationForm(FlaskForm):
    db_type = StringField('Type')
    environment = StringField('Environment')
    hostname = StringField('Hostname')
    instance_ownership = StringField('Instance Ownership (Shared | Dedicated)')
    os = StringField('Operating System')
    database_platform = StringField('Database Platform')
    version = StringField('Version')
    auth_type = StringField('Auth Type')
    instance_name = StringField('Instance Name(s)')
    service_account_name = StringField('Service Account Name')
    data_classification = StringField('Data Classification')
    data_sovereignty = StringField('Data Sovereignty')

class PerformanceIndicatorsForm(FlaskForm):
    high_availability = BooleanField('Highly Available')
    ha_type = StringField('HA Type')
    business_health = StringField('Business Application Health')
    shared_service_list = TextAreaField('Shared Service List')

# Extending AppDiscoveryForm to include new fields
class AppDiscoveryForm(FlaskForm):
    app_overview = FormField(ApplicationOverviewForm)
    app_stakeholders = FieldList(FormField(ApplicationStakeholderForm), min_entries=1, max_entries=10)
    app_bus_cap_model = FormField(ApplicationBusCapModelForm)
    app_operation = FormField(ApplicationOperationForm)
    #network_information = FieldList(FormField(NetworkInformationForm), min_entries=1, max_entries=10)
    server_information = FieldList(FormField(ServerInformationForm), min_entries=1, max_entries=10)
    interfaces = FieldList(FormField(InterfacesForm), min_entries=1, max_entries=10)
    web_system = FormField(WebSystemInformationForm)
    database = FormField(DatabaseInformationForm)
    performance = FormField(PerformanceIndicatorsForm)
    submit = SubmitField('Submit')

# Home page
@app.route('/')
def home():
    logger.debug('Home route accessed')
    return render_template('home.html')

# Route for adding an application
@app.route('/add-application', methods=['GET', 'POST'])
def add_application():
    form = AppDiscoveryForm()
    logger.debug('Add application page accessed')

    if request.method == 'POST':
        logger.debug(f'Form POST request received with data: {form.data}')
        
        if form.validate_on_submit():
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
                #"network_information": [network.data for network in form.network_information],
                "server_information": [server.data for server in form.server_information],
                "interfaces": [interface.data for interface in form.interfaces],
                "web_system": form.web_system.data,
                "database": form.database.data,
                "performance": form.performance.data
            }

            logger.debug(f'Application data: {application_data}')
            
            try:
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

# Route for removing an application
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

# Route for editing an application
@app.route('/edit-application/<app_name>', methods=['GET', 'POST'])
def edit_application(app_name):
    try:
        app_item = container.read_item(item=app_name, partition_key=app_name)
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error fetching data for {app_name}: {e}")
        flash(f"Application {app_name} could not be found.", "error")
        return redirect(url_for('view_applications'))

    form = AppDiscoveryForm(data=app_item)

    if request.method == 'POST':
        logger.debug(f'Edit Form POST request received with data: {form.data}')
        
        if form.validate_on_submit():
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
                #"network_information": [network.data for network in form.network_information],
                "server_information": [server.data for server in form.server_information],
                "interfaces": [interface.data for interface in form.interfaces],
                "web_system": form.web_system.data,
                "database": form.database.data,
                "performance": form.performance.data
            }

            try:
                container.replace_item(item=app_name, body=updated_application_data)
                logger.info(f"Application {app_name} updated successfully.")
                flash(f"Application {app_name} updated successfully!", "success")
                return redirect(url_for('view_applications'))
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Error updating application: {e}")
                flash(f"Error updating application {app_name}: {e}", "error")

    return render_template('add_application.html', form=form, edit_mode=True, app_name=app_name)

#csv import export
# Export applications to CSV
# Export applications to CSV
# Export applications to CSV

def remove_unwanted_fields(application):
    """ Remove unnecessary fields from the application data recursively. """
    fields_to_remove = ["_ts", "_attachments", "_etag", "csrf_token","_rid", "_self"]
    
    # If it's a list, process each element
    if isinstance(application, list):
        return [remove_unwanted_fields(item) for item in application]
    
    # If it's a dictionary, remove specific fields
    if isinstance(application, dict):
        return {k: remove_unwanted_fields(v) for k, v in application.items() if k not in fields_to_remove}
    
    # Otherwise, return the value as is
    return application

def flatten_json(data, parent_key='', separator='_'):
    """ Flatten nested JSON data """
    items = []
    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_json(value, new_key, separator).items())
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    items.extend(flatten_json(item, f"{new_key}_{i}", separator).items())
                else:
                    items.append((f"{new_key}_{i}", item))
        else:
            items.append((new_key, value))
    return dict(items)

def ensure_all_keys(flattened_apps):
    """ Ensure all keys are consistent across all flattened applications """
    all_keys = set()
    for app in flattened_apps:
        all_keys.update(app.keys())

    # Add missing keys with empty values for consistency
    for app in flattened_apps:
        for key in all_keys:
            if key not in app:
                app[key] = ''  # Assign empty string for missing keys

    return list(all_keys), flattened_apps

# Updated Export Route
@app.route('/export-applications', methods=['GET'])
def export_applications():
    try:
        applications = list(container.read_all_items())
        # Clean and flatten each application
        flattened_applications = [flatten_json(remove_unwanted_fields(app)) for app in applications]

        # Ensure consistent keys across all applications
        all_keys, cleaned_flattened_apps = ensure_all_keys(flattened_applications)

        # Create CSV output
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=all_keys, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Write the header and the rows
        writer.writeheader()
        writer.writerows(cleaned_flattened_apps)

        # Get the content of the StringIO as a bytes object
        csv_content = output.getvalue().encode('utf-8')
        output.close()

        # Create a BytesIO stream from the CSV content
        result = BytesIO(csv_content)
        result.seek(0)

        return send_file(result, mimetype='text/csv', as_attachment=True, download_name='applications.csv')
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error exporting data from Cosmos DB: {e}")
        flash("An error occurred while exporting applications.", "error")
        return redirect(url_for('view_applications'))



def resolve_conflicting_keys(data, conflict_keys, default_value=""):
    """
    Resolves conflicts in the provided nested dictionary for specific conflicting keys.
    Retains dictionaries and replaces conflicting non-dictionary values with the default value.
    """
    if isinstance(data, list):
        return [resolve_conflicting_keys(item, conflict_keys, default_value) for item in data]

    if isinstance(data, dict):
        cleaned_data = {}
        for key, value in data.items():
            if key in conflict_keys:
                if isinstance(value, dict):
                    # If the value is already a dictionary, retain it
                    cleaned_data[key] = resolve_conflicting_keys(value, conflict_keys, default_value)
                elif key in cleaned_data and isinstance(cleaned_data[key], dict):
                    # Existing value is a dictionary, so skip or overwrite appropriately
                    logger.warning(f"Conflicting key '{key}' already contains a dictionary. Ignoring new non-dict value.")
                else:
                    # If conflicting key contains a non-dictionary value, nullify or replace with default
                    logger.debug(f"Setting default value for conflicting key '{key}' with non-dict value.")
                    cleaned_data[key] = default_value
            else:
                # Recursively clean nested dictionaries
                cleaned_data[key] = resolve_conflicting_keys(value, conflict_keys, default_value)
        return cleaned_data

    # For other data types, return the value as it is
    return data

def unflatten_json(data, separator='_'):
    """ Convert flattened JSON back to its nested format """
    result = {}
    for key, value in data.items():
        if not key.strip():  # Ignore empty keys
            logger.warning(f"Skipping empty key for value: {value}")
            continue

        keys = key.split(separator)
        d = result
        for part in keys[:-1]:
            if part not in d:
                d[part] = {}
            elif not isinstance(d[part], dict):
                logger.error(f"Conflict: '{part}' in '{key}' is not a dictionary. Overwriting with a new dictionary.")
                d[part] = {}  # Overwrite non-dictionary with a new dictionary

            d = d[part]

        try:
            if isinstance(d, dict):
                if keys[-1] in d and isinstance(d[keys[-1]], dict) and not isinstance(value, dict):
                    logger.error(f"Conflict detected at key '{keys[-1]}'. Existing value is a dict, new value is not.")
                    # Handle the conflict appropriately, e.g., skip or overwrite
                else:
                    d[keys[-1]] = value
            else:
                logger.error(f"Attempting to assign a key to a non-dictionary object: {d}")
        except Exception as e:
            logger.error(f"Failed to assign value for key '{keys[-1]}' with error: {e}")

    return result



# Conflicting keys to handle specifically
conflicting_keys = ["os"]

# Use the updated function in your import logic as shown in previous messages.

@app.route('/import-applications', methods=['POST'])
def import_applications():
    csv_file = request.files['csv_file']
    app.logger.info(f"Received file: {csv_file.filename}")

    try:
        # Read the CSV content
        content = csv_file.read().decode('utf-8')
        app.logger.info(f"File content preview: {content[:200]}")  # Log the first 200 characters to check the file content

        # Use StringIO to treat the string as a file object
        csv_io = io.StringIO(content)
        
        # Parse CSV with the csv module
        csv_reader = csv.DictReader(csv_io)
        if csv_reader.fieldnames:
            app.logger.info(f"CSV columns: {csv_reader.fieldnames}")  # Log column headers
            
            for row in csv_reader:
                # Map CSV data into the required structure
                application_data = {
                    "id": row.get("app_name", "default_id"),
                    "app_name": row.get("app_name", ""),
                    "app_overview": {
                        "app_name": row.get("app_name", ""),
                        "app_desc_full": row.get("app_overview_app_desc_full", ""),
                        "app_desc_one_liner": row.get("app_overview_app_desc_one_liner", None),
                        "app_type": row.get("app_overview_app_type", ""),
                        "app_age": row.get("app_overview_app_age", ""),
                        "app_version": row.get("app_overview_app_version", ""),
                        "app_runtime_lang": row.get("app_overview_app_runtime_lang", None),
                        "app_complexity": row.get("app_overview_app_complexity", ""),
                        "app_support": row.get("app_overview_app_support", ""),
                        "app_env": row.get("app_overview_app_env", None),
                        "app_exists": row.get("app_overview_app_exists", "").lower() == 'true',
                        "other_runtime_lang": row.get("app_overview_other_runtime_lang", None),
                        "business_details": {
                            "business_owner": row.get("app_overview_business_details_business_owner", ""),
                            "business_purpose": row.get("app_overview_business_details_business_purpose", ""),
                            "business_criticality": row.get("app_overview_business_details_business_criticality", None),
                            "business_impact": row.get("app_overview_business_details_business_impact", None)
                        },
                        "application_meta": {
                            "number_of_users": row.get("app_overview_application_meta_number_of_users", None),
                            "release_freq": row.get("app_overview_application_meta_release_freq", ""),
                            "work_hours_stand": row.get("app_overview_application_meta_work_hours_stand", ""),
                            "planned_reg_downtime": row.get("app_overview_application_meta_planned_reg_downtime", ""),
                            "documentation": row.get("app_overview_application_meta_documentation", "")
                        }
                    },
                    "app_stakeholders": [
                        {
                            "stakeholder_name": row.get("app_stakeholders_0_stakeholder_name", ""),
                            "contact_type": row.get("app_stakeholders_0_contact_type", ""),
                            "business_unit": row.get("app_stakeholders_0_business_unit", ""),
                            "department": row.get("app_stakeholders_0_department", ""),
                            "number": row.get("app_stakeholders_0_number", ""),
                            "email": row.get("app_stakeholders_0_email", ""),
                            "position": row.get("app_stakeholders_0_position", ""),
                            "csrf_token": None
                        }
                    ],
                    "app_bus_cap_model": {
                        "capability_model": row.get("app_bus_cap_model_capability_model", ""),
                        "front_office": row.get("app_bus_cap_model_front_office", "").lower() == 'true',
                        "back_office": row.get("app_bus_cap_model_back_office", "").lower() == 'true',
                        "middle_office": row.get("app_bus_cap_model_middle_office", "").lower() == 'true',
                        "it_for_it": row.get("app_bus_cap_model_it_for_it", "").lower() == 'true',
                        "enterprise": row.get("app_bus_cap_model_enterprise", "").lower() == 'true',
                        "not_mapped": row.get("app_bus_cap_model_not_mapped", "").lower() == 'true',
                        "csrf_token": None
                    },
                    "app_operation": {
                        "high_availability": row.get("app_operation_high_availability", "").lower() == 'true',
                        "disaster_recovery": row.get("app_operation_disaster_recovery", "").lower() == 'true',
                        "rto": row.get("app_operation_rto", ""),
                        "rpo": row.get("app_operation_rpo", ""),
                        "csrf_token": None
                    }
                }

                # Continue to Part 2
                application_data.update({
                    "server_information": [
                        {
                            "environment": row.get("server_information_0_environment", ""),
                            "hostname": row.get("server_information_0_hostname", ""),
                            "role": row.get("server_information_0_role", ""),
                            "platform_type": row.get("server_information_0_platform_type", ""),
                            "shared_or_dedicated": row.get("server_information_0_shared_or_dedicated", ""),
                            "os": row.get("server_information_0_os", ""),
                            "os_features": row.get("server_information_0_os_features", ""),
                            "cpu": row.get("server_information_0_cpu", ""),
                            "ram": row.get("server_information_0_ram", ""),
                            "os_disk_gb": row.get("server_information_0_os_disk_gb", None),
                            "data_disk_count": row.get("server_information_0_data_disk_count", None),
                            "shared_data_store": row.get("server_information_0_shared_data_store", ""),
                            "network_environment": row.get("server_information_0_network_environment", ""),
                            "network_hostname": row.get("server_information_0_network_hostname", ""),
                            "network_name": row.get("server_information_0_network_name", ""),
                            "subnet": row.get("server_information_0_subnet", ""),
                            "ip_address": row.get("server_information_0_ip_address", ""),
                            "csrf_token": None
                        }
                    ],
                    "interfaces": [
                        {
                            "source_app": row.get("interfaces_0_source_app", ""),
                            "target_app": row.get("interfaces_0_target_app", ""),
                            "direction": row.get("interfaces_0_direction", ""),
                            "frequency": row.get("interfaces_0_frequency", ""),
                            "mechanism": row.get("interfaces_0_mechanism", ""),
                            "trigger": row.get("interfaces_0_trigger", ""),
                            "bandwidth": row.get("interfaces_0_bandwidth", ""),
                            "protcol": row.get("interfaces_0_protcol", ""),
                            "other_system_owner": row.get("interfaces_0_other_system_owner", None),
                            "csrf_token": None
                        }
                    ],
                    "web_system": {
                        "environment": row.get("web_system_environment", ""),
                        "internet_access": row.get("web_system_internet_access", ""),
                        "external_access": row.get("web_system_external_access", ""),
                        "web_server": row.get("web_system_web_server", ""),
                        "public_ips": row.get("web_system_public_ips", ""),
                        "authentication": row.get("web_system_authentication", ""),
                        "authorization": row.get("web_system_authorization", ""),
                        "load_balanced": row.get("web_system_load_balanced", "").lower() == 'true',
                        "url": row.get("web_system_url", ""),
                        "certificate": row.get("web_system_certificate", ""),
                        "csrf_token": None
                    },
                    "database": {
                        "db_type": row.get("database_db_type", ""),
                        "environment": row.get("database_environment", ""),
                        "hostname": row.get("database_hostname", ""),
                        "instance_ownership": row.get("database_instance_ownership", ""),
                        "os": row.get("database_os", ""),
                        "database_platform": row.get("database_database_platform", ""),
                        "version": row.get("database_version", ""),
                        "auth_type": row.get("database_auth_type", ""),
                        "instance_name": row.get("database_instance_name", ""),
                        "service_account_name": row.get("database_service_account_name", ""),
                        "data_classification": row.get("database_data_classification", ""),
                        "data_sovereignty": row.get("database_data_sovereignty", ""),
                        "csrf_token": None
                    },
                    "performance": {
                        "high_availability": row.get("performance_high_availability", "").lower() == 'true',
                        "ha_type": row.get("performance_ha_type", ""),
                        "business_health": row.get("performance_business_health", ""),
                        "shared_service_list": row.get("performance_shared_service_list", ""),
                        "csrf_token": None
                    }
                })

                # Log the mapped data before inserting to Cosmos DB
                app.logger.info(f"Mapped Application Data: {application_data}")

                # Check if the document exists
                try:
                    existing_item = container.read_item(item=row.get("app_name"), partition_key=row.get("app_name"))
                    app.logger.info(f"Existing item found, updating: {existing_item['id']}")
                    
                    # Update existing item
                    container.replace_item(item=existing_item['id'], body=application_data)
                
                except exceptions.CosmosResourceNotFoundError:
                    # If item does not exist, create a new one
                    app.logger.info(f"No existing item found. Creating new item: {application_data['id']}")
                    container.create_item(body=application_data)

        else:
            app.logger.error("No column headers found in CSV file.")

    except Exception as e:
        app.logger.error(f"Error during CSV import: {e}")

    return redirect(url_for('view_applications'))

if __name__ == '__main__':
    app.run(debug=True)
