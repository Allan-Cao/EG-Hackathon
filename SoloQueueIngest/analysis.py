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

db = client["league_data"]
collection = db["solo_queue_data"]

pipeline = [
    {
        "$match": {
            "player_name": "C9 Fudge",
            "data_type": "PARTICIPANT"
        }
    },
    {
        "$group": {
            "_id": "$game_id",
            "total_kills": {"$sum": "$data.kills"}
        }
    },
    {
        "$group": {
            "_id": None,
            "average_kills_per_game": {"$avg": "$total_kills"}
        }
    }
]

result = list(db.your_collection_name.aggregate(pipeline))

if result:
    average_kills = result[0]["average_kills_per_game"]
else:
    average_kills = 0  # Player not found or no data available

print("Average Kills per Game for C9 Fudge:", average_kills)
