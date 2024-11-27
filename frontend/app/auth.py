import os
import logging
from azure.cosmos import CosmosClient, exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session, redirect, url_for, flash, request
from functools import wraps
import uuid

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app.auth")

# Initialize Cosmos DB client
cosmos_endpoint = os.getenv("COSMOS_URI")
cosmos_key = os.getenv("COSMOS_KEY")
database_name = "apppassports"
users_container_name = "users"
roles_container_name = "roles"

# Cosmos DB client and container setup
cosmos_client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
database = cosmos_client.get_database_client(database_name)
users_container = database.get_container_client(users_container_name)
roles_container = database.get_container_client(roles_container_name)

# auth.py

def application_access_required(role, app_id_key="app_id"):
    """
    Decorator to restrict access based on user role and specific app permissions.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("user_role")
            user_id = session.get("user_id")
            app_id = kwargs.get(app_id_key)  # Get app_id from route parameters

            if user_role != role:
                flash("Access denied: insufficient permissions", "error")
                return redirect(url_for("login", next=request.url))
            
            # Check if the user has access to the specified app
            if app_id:
                user = find_user_by_id(user_id)  # Add this helper function
                if user and app_id not in user.get("assigned_apps", []):
                    flash("Access denied: You do not have access to this application.", "error")
                    return redirect(url_for("home"))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def list_all_users():
    """
    Logs all users in the Cosmos DB 'users' container for debugging purposes.
    """
    try:
        all_users = list(users_container.read_all_items())
        logger.debug("Listing all users in Cosmos DB 'users' container:")
        for user in all_users:
            username = user.get("username", "Unknown")
            logger.debug(f"User in container: ID: {user['id']}, Username: {username}")
    except exceptions.CosmosResourceNotFoundError:
        logger.error("Container not found. Please check your Cosmos DB setup.")
    except Exception as e:
        logger.error(f"An error occurred while listing all users: {e}")

def find_user_by_username(username):
    """
    Queries the Cosmos DB 'users' container to find a user by username.
    """
    try:
        query = "SELECT * FROM users u WHERE u.username = @username"
        parameters = [{"name": "@username", "value": username}]
        items = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        if items:
            user = items[0]
            logger.debug(f"Found user: {user}")
            return user
        else:
            logger.warning(f"No user found with username: {username}")
            return None
    except Exception as e:
        logger.error(f"An error occurred while querying for user '{username}': {e}")
        return None

def verify_password(stored_password_hash, provided_password):
    """
    Verifies the password using a hashed password comparison.
    """
    return check_password_hash(stored_password_hash, provided_password)

def create_user_with_role(username, password, role="user"):
    """
    Creates a user in the Cosmos DB 'users' container and assigns a role in the 'roles' container.
    """
    try:
        existing_user = find_user_by_username(username)
        if existing_user:
            logger.warning(f"User {username} already exists.")
            return False

        password_hash = generate_password_hash(password)
        user_id = str(uuid.uuid4())
        new_user = {
            "id": user_id,
            "username": username,
            "password_hash": password_hash
        }
        users_container.create_item(new_user)
        logger.info(f"User {username} created successfully in the users container.")

        new_role = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "role": role
        }
        roles_container.create_item(new_role)
        logger.info(f"Role '{role}' assigned to user {username} in roles container.")
        return True

    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error interacting with Cosmos DB while creating user '{username}': {e}")
        return False

def login_user(username, password):
    """
    Handles the login logic for a user, including retrieving their role and assigned applications.
    """
    list_all_users()

    user = find_user_by_username(username)
    if user:
        if verify_password(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            try:
                logger.debug(f"Attempting to retrieve role for user ID: {user['id']}")
                query = "SELECT * FROM roles r WHERE r.user_id = @user_id"
                parameters = [{"name": "@user_id", "value": user["id"]}]
                roles = list(roles_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
                
                # Set the user role in session
                role = roles[0].get("role", "user") if roles else "user"
                session["user_role"] = role
                logger.info(f"User '{username}' logged in successfully with role '{role}'.")

                # Retrieve assigned applications
                assigned_apps = user.get("assigned_apps", [])
                session["assigned_apps"] = assigned_apps  # Store in session for access control

                logger.debug(f"User '{username}' has access to applications: {assigned_apps}")

            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Error fetching role for user '{username}': {e}")
                session["user_role"] = "user"  # Default role
                session["assigned_apps"] = []  # No applications assigned by default
            
            return True
        else:
            logger.warning("Invalid password provided.")
            return False
    else:
        logger.warning(f"No user found with username: {username}")
        return False

def role_required(role):
    """
    Decorator to restrict access to users with a specific role.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("user_role")
            logger.debug(f"Accessing protected route, user role in session: {user_role}")

            if user_role != role:
                flash("Access denied: insufficient permissions", "error")
                return redirect(url_for("login", next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def logout_user():
    """
    Logs out the current user by clearing the session.
    """
    session.clear()
    logger.info("User logged out successfully.")

def is_logged_in():
    """Check if the user is logged in."""
    return "username" in session

def get_logged_in_user():
    """Get the username of the currently logged-in user."""
    return session.get("username", "Guest")


def find_user_by_id(user_id):
    """
    Queries the Cosmos DB 'users' container to find a user by user_id.
    """
    try:
        query = "SELECT * FROM users u WHERE u.id = @user_id"
        parameters = [{"name": "@user_id", "value": user_id}]
        items = list(users_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        if items:
            user = items[0]
            logger.debug(f"Found user by ID: {user}")
            return user
        else:
            logger.warning(f"No user found with ID: {user_id}")
            return None
    except Exception as e:
        logger.error(f"An error occurred while querying for user ID '{user_id}': {e}")
        return None
