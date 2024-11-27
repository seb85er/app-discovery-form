# importexport.py
import os
from azure.cosmos import CosmosClient, exceptions
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from app import app  # Import the app instance from app/__init__.py
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, BooleanField, IntegerField, FieldList, FormField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional
from io import BytesIO, StringIO
import csv
import io

logger = logging.getLogger(__name__)
logger.debug('importexport are being registered.')
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


conflicting_keys = ["os"]


@app.route('/import-applications', methods=['POST'])
def import_applications():
    csv_file = request.files['csv_file']
    app.logger.info(f"Received file: {csv_file.filename}")

    try:
        # Read the CSV content
        content = csv_file.read().decode('utf-8')
        app.logger.info(f"File content preview: {content[:200]}")  # Log the first 200 characters

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
                    }
                }

                # Handle multiple app_stakeholders entries
                app_stakeholders = []
                stakeholder_index = 0
                while True:
                    stakeholder_prefix = f"app_stakeholders_{stakeholder_index}_"
                    if any(key.startswith(stakeholder_prefix) for key in row.keys()):
                        stakeholder = {
                            "stakeholder_name": row.get(f"{stakeholder_prefix}stakeholder_name", ""),
                            "contact_type": row.get(f"{stakeholder_prefix}contact_type", ""),
                            "business_unit": row.get(f"{stakeholder_prefix}business_unit", ""),
                            "department": row.get(f"{stakeholder_prefix}department", ""),
                            "number": row.get(f"{stakeholder_prefix}number", ""),
                            "email": row.get(f"{stakeholder_prefix}email", ""),
                            "position": row.get(f"{stakeholder_prefix}position", "")
                        }
                        if any(stakeholder.values()):
                            app_stakeholders.append(stakeholder)
                        stakeholder_index += 1
                    else:
                        break
                application_data["app_stakeholders"] = app_stakeholders

                # Handle multiple server_information entries
                server_info_list = []
                server_index = 0
                while True:
                    server_prefix = f"server_information_{server_index}_"
                    if any(key.startswith(server_prefix) for key in row.keys()):
                        server_info = {
                            "environment": row.get(f"{server_prefix}environment", ""),
                            "hostname": row.get(f"{server_prefix}hostname", ""),
                            "role": row.get(f"{server_prefix}role", ""),
                            "platform_type": row.get(f"{server_prefix}platform_type", ""),
                            "shared_or_dedicated": row.get(f"{server_prefix}shared_or_dedicated", ""),
                            "os": row.get(f"{server_prefix}os", ""),
                            "os_features": row.get(f"{server_prefix}os_features", ""),
                            "cpu": row.get(f"{server_prefix}cpu", ""),
                            "ram": row.get(f"{server_prefix}ram", ""),
                            "os_disk_gb": row.get(f"{server_prefix}os_disk_gb", None),
                            "data_disk_count": row.get(f"{server_prefix}data_disk_count", None),
                            "shared_data_store": row.get(f"{server_prefix}shared_data_store", ""),
                            "network_environment": row.get(f"{server_prefix}network_environment", ""),
                            "network_hostname": row.get(f"{server_prefix}network_hostname", ""),
                            "network_name": row.get(f"{server_prefix}network_name", ""),
                            "subnet": row.get(f"{server_prefix}subnet", ""),
                            "ip_address": row.get(f"{server_prefix}ip_address", "")
                        }
                        if any(server_info.values()):
                            server_info_list.append(server_info)
                        server_index += 1
                    else:
                        break
                application_data["server_information"] = server_info_list

                # Handle multiple interfaces entries
                interfaces_list = []
                interface_index = 0
                while True:
                    interface_prefix = f"interfaces_{interface_index}_"
                    if any(key.startswith(interface_prefix) for key in row.keys()):
                        interface_info = {
                            "source_app": row.get(f"{interface_prefix}source_app", ""),
                            "target_app": row.get(f"{interface_prefix}target_app", ""),
                            "direction": row.get(f"{interface_prefix}direction", ""),
                            "frequency": row.get(f"{interface_prefix}frequency", ""),
                            "mechanism": row.get(f"{interface_prefix}mechanism", ""),
                            "trigger": row.get(f"{interface_prefix}trigger", ""),
                            "bandwidth": row.get(f"{interface_prefix}bandwidth", ""),
                            "protcol": row.get(f"{interface_prefix}protcol", "")
                        }
                        if any(interface_info.values()):
                            interfaces_list.append(interface_info)
                        interface_index += 1
                    else:
                        break
                application_data["interfaces"] = interfaces_list

                # Handle multiple web_system entries
                web_systems = []
                web_system_index = 0
                while True:
                    web_system_prefix = f"web_system_{web_system_index}_"
                    if any(key.startswith(web_system_prefix) for key in row.keys()):
                        web_system = {
                            "environment": row.get(f"{web_system_prefix}environment", ""),
                            "internet_access": row.get(f"{web_system_prefix}internet_access", ""),
                            "external_access": row.get(f"{web_system_prefix}external_access", ""),
                            "web_server": row.get(f"{web_system_prefix}web_server", ""),
                            "public_ips": row.get(f"{web_system_prefix}public_ips", ""),
                            "authentication": row.get(f"{web_system_prefix}authentication", ""),
                            "authorization": row.get(f"{web_system_prefix}authorization", ""),
                            "load_balanced": row.get(f"{web_system_prefix}load_balanced", "").lower() == 'true',
                            "url": row.get(f"{web_system_prefix}url", ""),
                            "certificate": row.get(f"{web_system_prefix}certificate", "")
                        }
                        if any(web_system.values()):
                            web_systems.append(web_system)
                        web_system_index += 1
                    else:
                        break
                application_data["web_system"] = web_systems

                # Handle multiple database entries
                databases = []
                database_index = 0
                while True:
                    database_prefix = f"database_{database_index}_"
                    if any(key.startswith(database_prefix) for key in row.keys()):
                        database = {
                            "db_type": row.get(f"{database_prefix}db_type", ""),
                            "environment": row.get(f"{database_prefix}environment", ""),
                            "hostname": row.get(f"{database_prefix}hostname", ""),
                            "instance_ownership": row.get(f"{database_prefix}instance_ownership", ""),
                            "os": row.get(f"{database_prefix}os", ""),
                            "database_platform": row.get(f"{database_prefix}database_platform", ""),
                            "version": row.get(f"{database_prefix}version", ""),
                            "auth_type": row.get(f"{database_prefix}auth_type", ""),
                            "instance_name": row.get(f"{database_prefix}instance_name", ""),
                            "service_account_name": row.get(f"{database_prefix}service_account_name", ""),
                            "data_classification": row.get(f"{database_prefix}data_classification", ""),
                            "data_sovereignty": row.get(f"{database_prefix}data_sovereignty", "")
                        }
                        if any(database.values()):
                            databases.append(database)
                        database_index += 1
                    else:
                        break
                application_data["database"] = databases

                # Handle performance information
                application_data["performance"] = {
                    "high_availability": row.get("performance_high_availability", "").lower() == 'true',
                    "ha_type": row.get("performance_ha_type", ""),
                    "business_health": row.get("performance_business_health", ""),
                    "shared_service_list": row.get("performance_shared_service_list", "")
                }

                # Log the mapped data before inserting to Cosmos DB
                app.logger.info(f"Mapped Application Data: {application_data}")

                # Check if the document exists
                try:
                    existing_item = container.read_item(item=application_data["id"], partition_key=application_data["id"])
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
