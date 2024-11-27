# routes.py
import os
import logging
import uuid  # For generating unique user IDs
from werkzeug.security import generate_password_hash  # For hashing passwords
from flask import render_template, redirect, url_for, request, flash, session
from app import app
from app.forms import AppDiscoveryForm, LoginForm, CreateUserForm
from app.auth import role_required, login_user, logout_user, cosmos_client  # Import `cosmos_client` from `auth.py`
from azure.cosmos import exceptions,CosmosClient

logger = logging.getLogger(__name__)
logger.debug('Routes are being registered.')

COSMOS_DB_NAME = os.getenv('COSMOS_DB_NAME')
COSMOS_CONTAINER_NAME = os.getenv('COSMOS_CONTAINER_NAME')
database_name = os.getenv("COSMOS_DB_NAME")
cosmos_client = CosmosClient(os.getenv("COSMOS_URI"), credential=os.getenv("COSMOS_KEY"))


# Initialize primary container for general app data
database = cosmos_client.get_database_client(COSMOS_DB_NAME)
container = database.get_container_client(COSMOS_CONTAINER_NAME)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    next_page = request.args.get('next')

    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if login_user(username, password):
            return redirect(next_page or url_for('home'))
        else:
            flash("Invalid username or password.", "error")

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()  # Clears the session to log out the user
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/admin", methods=["GET", "POST"])
@role_required("admin")
def admin_dashboard():
    form = CreateUserForm()
    users_with_roles = []

    # Access users and roles containers
    try:
        users_container = cosmos_client.get_database_client(database_name).get_container_client("users")
        roles_container = cosmos_client.get_database_client(database_name).get_container_client("roles")
        
        # Fetch all users from the users container
        users = list(users_container.read_all_items())
        logger.debug("Fetched users: %s", users)

        # Populate users_with_roles with roles from roles_container
        for user in users:
            query = "SELECT * FROM roles r WHERE r.user_id = @user_id"
            parameters = [{"name": "@user_id", "value": user["id"]}]
            role_items = list(roles_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
            role = role_items[0]["role"] if role_items else "user"  # Default to "user" if no role found
            users_with_roles.append({"username": user.get("username", "Unknown"), "role": role})
        logger.info("Fetched all users with roles for admin view.")
    
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error fetching users or roles from Cosmos DB: {e}")
        flash("Error accessing Cosmos DB for users or roles.", "error")
    
    # Handle form submission for creating new users
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        role = form.role.data
        logger.info(f"Creating user with username: {username}, role: {role}")

        # Generate user ID and hashed password
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)

        # Create new user in users container
        user_data = {
            "id": user_id,
            "username": username,
            "password_hash": password_hash,
        }
        try:
            users_container.create_item(body=user_data)
            logger.info(f"User '{username}' created successfully in users container.")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error creating user '{username}': {e}")
            flash(f"Error creating user '{username}'.", "error")
            return redirect(url_for("admin_dashboard"))

        # Assign role to the user in the roles container
        role_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "role": role,
        }
        try:
            roles_container.create_item(body=role_data)
            logger.info(f"Role '{role}' assigned to user '{username}' in roles container.")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error assigning role '{role}' to user '{username}': {e}")
            flash(f"Error assigning role to '{username}'.", "error")
            return redirect(url_for("admin_dashboard"))

        flash(f"User '{username}' created successfully with role '{role}'.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin.html", form=form, users_with_roles=users_with_roles)


@app.route('/add-application', methods=['GET', 'POST'])
#@role_required('admin') 
def add_application():
    form = AppDiscoveryForm()
    logger.debug('Add application page accessed')

    if request.method == 'POST':
        logger.debug(f'Form POST request received with data: {form.data}')
        
        if form.validate_on_submit():
            logger.debug("Form validation passed.")

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
                "web_system": [web_system.data for web_system in form.web_system],
                "database": [database.data for database in form.database],
                "performance": form.performance.data
            }

            logger.debug(f'Application data to be saved: {application_data}')
            
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
        app_item = container.read_item(item=app_name, partition_key=app_name)
        logger.debug(f"Fetched application {app_name} from Cosmos DB: {app_item}")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error fetching data for {app_name}: {e}")
        flash(f"Application {app_name} could not be found.", "error")
        return redirect(url_for('view_applications'))

    form = AppDiscoveryForm(data=app_item)

    if request.method == 'POST':
        logger.debug(f'Edit Form POST request received with data: {form.data}')
        
        if form.validate_on_submit():
            logger.debug("Form validation passed.")

            updated_application_data = {
                "id": form.app_overview.app_name.data,
                "app_name": form.app_overview.app_name.data,
                "app_overview": {
                    # [Fields with updated data here]
                },
                # [More nested data here]
            }

            logger.debug(f'Updated application data to be saved: {updated_application_data}')
            
            try:
                container.replace_item(item=app_name, body=updated_application_data)
                logger.info(f"Application {app_name} updated successfully.")
                flash(f"Application {app_name} updated successfully!", "success")
                return redirect(url_for('view_applications'))
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Error updating application: {e}")
                flash(f"Error updating application {app_name}: {e}", "error")

    return render_template('add_application.html', form=form, edit_mode=True, app_name=app_name)
