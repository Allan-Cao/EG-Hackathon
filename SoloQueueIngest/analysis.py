from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
import csv
import requests as r
champions = r.get('https://ddragon.leagueoflegends.com/cdn/13.20.1/data/en_US/champion.json').json()
champion_map = {key: champions['data'][key]['name'] for key in champions['data'].keys()}

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
            "data_type": "PARTICIPANT"
        }
    },
    {
        "$group": {
            "_id": {"player": "$player_name", "champion": "$data.championName", "position": "$data.teamPosition"},
            "avgKills": {"$avg": "$data.stats.kills"},
            "avgDeaths": {"$avg": "$data.stats.deaths"},
            "avgAssists": {"$avg": "$data.stats.assists"},
            "gamesPlayed": {"$sum": 1}
        }
    },
    {
    "$addFields": {
        "avgKDA": {
            "$divide": [
                {"$add": ["$avgKills", "$avgAssists"]},
                {"$max": ["$avgDeaths", 1]}
            ]
        },
            "player_name": "$player_name"
        },
    },
    {
        "$sort": {
            "gamesPlayed": -1
        }
    }
]

result = list(collection.aggregate(pipeline))

# Define CSV file and headers
with open('player_stats.csv', 'w', newline='') as csvfile:
    fieldnames = ['player_name', 'champion', 'position', 'avgKills', 'avgDeaths', 'avgAssists', 'avgKDA', 'gamesPlayed']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    # Write data to CSV
    for entry in result:
        row_data = {
            'player_name': entry['_id']['player'],
            'champion': champion_map[entry['_id']['champion']],
            'position': entry['_id']['position'],
            'avgKills': entry['avgKills'],
            'avgDeaths': entry['avgDeaths'],
            'avgAssists': entry['avgAssists'],
            'avgKDA': entry['avgKDA'],
            'gamesPlayed': entry['gamesPlayed']
        }
        writer.writerow(row_data)
