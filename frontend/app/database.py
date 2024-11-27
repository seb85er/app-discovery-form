import os
from azure.cosmos import CosmosClient

# Get Cosmos DB configuration from environment variables
COSMOS_URI = os.getenv('COSMOS_URI')
COSMOS_KEY = os.getenv('COSMOS_KEY')
COSMOS_DB_NAME = os.getenv('COSMOS_DB_NAME')
COSMOS_CONTAINER_NAME = os.getenv('COSMOS_CONTAINER_NAME')

# Initialize Cosmos client
client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)
database = client.get_database_client(COSMOS_DB_NAME)
container = database.get_container_client(COSMOS_CONTAINER_NAME)
