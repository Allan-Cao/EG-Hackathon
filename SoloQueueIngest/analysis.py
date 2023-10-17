from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Initialize env variables
load_dotenv()
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Initialize MongoDB
uri = f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@egch.zp99gng.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi("1"))

# Check MongoDB connection
try:
    client.admin.command("ping")
    print("Connected to MongoDB!")
except Exception as e:
    print(e)
    exit()