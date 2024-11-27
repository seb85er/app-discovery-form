#forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, FieldList, FormField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

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
    server_information = FieldList(FormField(ServerInformationForm), min_entries=1, max_entries=10)
    interfaces = FieldList(FormField(InterfacesForm), min_entries=1, max_entries=10)
    web_system = FieldList(FormField(WebSystemInformationForm), min_entries=1, max_entries=10)  # Changed to FieldList
    database = FieldList(FormField(DatabaseInformationForm), min_entries=1, max_entries=10)  # Changed to FieldList
    performance = FormField(PerformanceIndicatorsForm)
    submit = SubmitField('Submit')

class AppDiscoveryForm(FlaskForm):
    app_overview = FormField(ApplicationOverviewForm)
    app_stakeholders = FieldList(FormField(ApplicationStakeholderForm), min_entries=1, max_entries=10)
    app_bus_cap_model = FormField(ApplicationBusCapModelForm)
    app_operation = FormField(ApplicationOperationForm)
    server_information = FieldList(FormField(ServerInformationForm), min_entries=1, max_entries=10)
    interfaces = FieldList(FormField(InterfacesForm), min_entries=1, max_entries=10)
    web_system = FieldList(FormField(WebSystemInformationForm), min_entries=1, max_entries=10)  # Changed to FieldList
    database = FieldList(FormField(DatabaseInformationForm), min_entries=1, max_entries=10)  # Changed to FieldList
    performance = FormField(PerformanceIndicatorsForm)
    submit = SubmitField('Submit')