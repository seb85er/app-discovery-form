import os
import logging
from werkzeug.security import generate_password_hash
from azure.cosmos import CosmosClient, exceptions
import uuid

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get Cosmos DB configuration from environment variables
COSMOS_URI = os.getenv('COSMOS_URI')
COSMOS_KEY = os.getenv('COSMOS_KEY')
COSMOS_DB_NAME = os.getenv('COSMOS_DB_NAME')
COSMOS_USERS_CONTAINER_NAME = 'users'
COSMOS_ROLES_CONTAINER_NAME = 'roles'

# Initialize Cosmos client
client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)
database = client.get_database_client(COSMOS_DB_NAME)
users_container = database.get_container_client(COSMOS_USERS_CONTAINER_NAME)
roles_container = database.get_container_client(COSMOS_ROLES_CONTAINER_NAME)

def create_admin_account(username, password):
    try:
        # Check if the user already exists
        query = f"SELECT * FROM c WHERE c.username = '{username}'"
        existing_users = list(users_container.query_items(query=query, enable_cross_partition_query=True))

        if existing_users:
            logger.warning(f"User {username} already exists.")
            return

        # Hash the password
        password_hash = generate_password_hash(password)

        # Generate a unique user ID
        user_id = str(uuid.uuid4())

        # Create the user in the users container
        new_user = {
            "id": user_id,
            "username": username,
            "password_hash": password_hash
        }
        users_container.create_item(new_user)
        logger.info(f"Admin user {username} created successfully.")

        # Assign the role to the user in the roles container
        new_role = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "role": "admin"
        }
        roles_container.create_item(new_role)
        logger.info(f"Role 'admin' assigned to user {username}.")

    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error interacting with Cosmos DB: {e}")

if __name__ == '__main__':
    # Replace these values with the desired username and password
    username = input("Enter the username for the admin account: ")
    password = input("Enter the password for the admin account: ")

    create_admin_account(username, password)
