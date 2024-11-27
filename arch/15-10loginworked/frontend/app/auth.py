import os
import logging
from azure.cosmos import CosmosClient, exceptions
from werkzeug.security import check_password_hash
from flask import session, redirect, url_for, flash
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app.auth")

# Initialize Cosmos DB client
cosmos_endpoint = os.getenv("COSMOS_URI")
cosmos_key = os.getenv("COSMOS_KEY")
database_name = "apppassports"
container_name = "users"

# Cosmos DB client and container setup
cosmos_client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
database = cosmos_client.get_database_client(database_name)
container = database.get_container_client(container_name)

def list_all_users():
    """
    Logs all users in the Cosmos DB 'users' container for debugging purposes.
    """
    try:
        all_users = list(container.read_all_items())
        logger.debug("Listing all users in Cosmos DB 'users' container:")
        for user in all_users:
            logger.debug(f"User in container: {user}")
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
        items = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
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

def login_user(username, password):
    """
    Handles the login logic for a user.
    """
    # Debug - List all users before querying
    list_all_users()

    # Find the user by username
    user = find_user_by_username(username)
    if user:
        # Verify the provided password with the stored hash
        if verify_password(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["user_role"] = user.get("role", "user")  # Default to 'user' if no role specified
            logger.info(f"User '{username}' logged in successfully.")
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
            if 'user_role' not in session or session['user_role'] != role:
                flash("Access denied: insufficient permissions", "error")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def logout_user():
    """
    Logs out the current user by clearing the session.
    """
    session.clear()
    logger.info("User logged out successfully.")
