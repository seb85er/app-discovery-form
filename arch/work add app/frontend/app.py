import os
import logging
from flask import Flask, render_template, redirect, url_for, request
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, BooleanField, IntegerField, FieldList, FormField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Optional
from azure.cosmos import CosmosClient, exceptions

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

# Initialize Cosmos client
client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)
database = client.get_database_client(COSMOS_DB_NAME)
container = database.get_container_client(COSMOS_CONTAINER_NAME)

# Define Forms
class ApplicationStakeholderForm(FlaskForm):
    name = StringField('Name')
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
    it_for_it = BooleanField('IT for IT')  # Add this missing field
    enterprise = BooleanField('Enterprise')  # Add this missing field
    not_mapped = BooleanField('Not Mapped')  # Add this missing field

class BusinessDetailsForm(FlaskForm):
    business_owner = StringField('Business Owner')
    business_purpose = StringField('Business Purpose')
    business_criticality = IntegerField('Business Criticality', validators=[Optional()])  # Optional integer field
    business_impact = IntegerField('Business Impact', validators=[Optional()])  # Optional integer field


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

class NetworkInformationForm(FlaskForm):
    environment = StringField('Environment')
    hostname = StringField('Hostname')
    network_name = StringField('Network Name')
    network_range = StringField('Network Range')
    subnet = StringField('Subnet')
    ip_address = StringField('IP Address')

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

class InterfacesForm(FlaskForm):
    source_app = StringField('Source App')
    target_app = StringField('Target App')
    direction = StringField('Direction')
    frequency = StringField('Frequency')  # Add this missing field
    mechanism = StringField('Mechanism')  # Add this missing field
    trigger = StringField('Trigger')  # Add this missing field
    bandwidth = StringField('Bandwidth')  # Add this missing field
    protcol = StringField('Protocol')  # Add this missing field
    other_system_owner = StringField('Other System Owner')

class ApplicationOverviewForm(FlaskForm):
    app_name = StringField('App Name', validators=[DataRequired()])
    app_desc_full = TextAreaField('App Description Full')
    app_desc_one_liner = StringField('App Description One Liner')
    app_type = StringField('App Type')
    app_age = StringField('App Age')  # Add this missing field
    app_version = StringField('App Version')
    app_runtime_lang = StringField('App Runtime Language')
    app_complexity = StringField('App Complexity')  # Add this missing field
    app_support = StringField('App Support')  # Add this missing field
    app_env = StringField('App Environment')
    app_exists = BooleanField('App Exists')
    other_runtime_lang = StringField('Other Runtime Language')
    business_details = FormField(BusinessDetailsForm)
    application_meta = FormField(ApplicationMetaForm)
    
class AppDiscoveryForm(FlaskForm):
    app_overview = FormField(ApplicationOverviewForm)
    app_stakeholders = FieldList(FormField(ApplicationStakeholderForm), min_entries=1, max_entries=10)
    app_bus_cap_model = FormField(ApplicationBusCapModelForm)
    app_operation = FormField(ApplicationOperationForm)
    network_information = FieldList(FormField(NetworkInformationForm), min_entries=1, max_entries=10)
    server_information = FieldList(FormField(ServerInformationForm), min_entries=1, max_entries=10)
    interfaces = FieldList(FormField(InterfacesForm), min_entries=1, max_entries=10)
    submit = SubmitField('Submit')

# Default landing page
@app.route('/')
def home():
    logger.debug('Home route accessed')
    return render_template('home.html')

# Route for the form to add an application
@app.route('/add-application', methods=['GET', 'POST'])
def add_application():
    form = AppDiscoveryForm()
    logger.debug('Add application page accessed')

    if request.method == 'POST':
        logger.debug(f'Form POST request received with data: {form.data}')
        
        if form.validate_on_submit():
            application_data = {
                "id": form.app_overview.app_name.data,  # Use app_name as the 'id'
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
                "network_information": [network.data for network in form.network_information],
                "server_information": [server.data for server in form.server_information],
                "interfaces": [interface.data for interface in form.interfaces],
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
    form = AppDiscoveryForm()  # This will provide the CSRF token
    try:
        applications = list(container.read_all_items())  # Fetch all items from Cosmos DB
        for app in applications:
            app['completion_percentage'], app['missing_fields'] = calculate_completion(app)  # Calculate percentage
        logger.info(f"Fetched {len(applications)} applications from Cosmos DB")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error fetching data from Cosmos DB: {e}")
        applications = []
    
    return render_template('view_applications.html', applications=applications, form=form)


def calculate_completion(application_data):
    total_fields = 0
    filled_fields = 0
    missing_fields = []

    def check_field(field, field_name):
        nonlocal total_fields, filled_fields
        total_fields += 1
        if field and (not isinstance(field, str) or field.strip()):  # Check for non-empty string or valid data
            filled_fields += 1
        else:
            missing_fields.append(field_name)

    # Check app overview fields
    app_overview = application_data.get("app_overview", {})
    for field_name, field_value in app_overview.items():
        check_field(field_value, field_name)

    # Similarly, check other fields like `app_stakeholders`, `app_bus_cap_model`, etc.
    for stakeholder in application_data.get("app_stakeholders", []):
        for field_name, field_value in stakeholder.items():
            check_field(field_value, f"stakeholder {field_name}")

    for server in application_data.get("server_information", []):
        for field_name, field_value in server.items():
            check_field(field_value, f"server {field_name}")

    # Add checks for other sections like `app_operation`, `network_information`, etc.

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


if __name__ == '__main__':
    app.run(debug=True)
