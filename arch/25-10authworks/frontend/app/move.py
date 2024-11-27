import os
from azure.cosmos import CosmosClient, exceptions

# Initialize Cosmos DB client
COSMOS_URI = os.getenv("COSMOS_URI")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "apppassports"
APPLICATIONS_CONTAINER_NAME = "applications"
USERS_CONTAINER_NAME = "users"

# Cosmos DB client setup
client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
applications_container = database.get_container_client(APPLICATIONS_CONTAINER_NAME)
users_container = database.get_container_client(USERS_CONTAINER_NAME)

def transfer_users():
    try:
        # Fetch all documents in the applications container
        documents = applications_container.read_all_items()
        
        for doc in documents:
            if "username" in doc and "password_hash" in doc:
                # Move user document to users container
                user_data = {
                    "id": doc["id"],
                    "username": doc["username"],
                    "password_hash": doc["password_hash"]
                }
                users_container.create_item(user_data)
                print(f"Transferred user '{doc['username']}' to users container.")

                # Optionally delete the user document from applications container
                applications_container.delete_item(item=doc["id"], partition_key=doc["id"])
                print(f"Removed user '{doc['username']}' from applications container.")

    except exceptions.CosmosHttpResponseError as e:
        print(f"Error during transfer: {e}")

if __name__ == "__main__":
    transfer_users()
