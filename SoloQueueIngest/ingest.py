import cassiopeia as cass
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Initialize env variables
load_dotenv()
API_KEY = os.getenv("RIOT_API")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Initialize Cassiopeia
cass.set_riot_api_key(API_KEY)

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


# Function to convert all keys in nested dict to string
def stringify_keys(d):
    if not isinstance(d, dict):
        return d
    return {str(k): stringify_keys(v) for k, v in d.items()}


# Get or Create DB and Collection
db = client["league_data"]
collection = db["solo_queue_data"]

# Get summoner and match history
players = {
    "Cy-3tKGgEC3rTVCqt7wyVPa8e7A9VyM2qs1QTfvd1ak-8DbXi54VdvgimDkOLY_zy5cCsn7XFO-Peg": "C9 Fudge",
    "11X6ZLZxFTynruyv9vm-tJ32biVyaIQluO0RWgLNA4DdRVKvdzM6eeyXXYweDe6BB4p2MxhY4t20kA": "C9 Blaber",
    "Ylz9L-LcXqY6ANnozHrCSvfKXYuj1tEMSTX8fn21ixMJSTlnHzErnxVbpu7TbReKZEI2o_QnWOsZ7w": "C9 EMENES",
    "YmAcSLJAnFDHX702V-OWjyaM3053yKViALQpYXB-DoI7EVTIIEn4D0ohsWj4kqp2kDDNtl3RzQZERQ": "C9 Berserker",
    "6uq3q67SLj0f6DKgRtSfwZBjL6do-s5W6P637pKkGt-y1KAKnqnK7WKrfmpAc8vIpHTsMNrXEEHHBA": "C9 Zven",
    "_Ar2qLJlEZEloNlSW9UxnsSGUooOGQH9Ur_WLkfQBjDsNKa0UsyDOrxtsWleUNL7nT51lWi8JaOEnw": "GG Licorice",
    "YVwQeLi8zuD40-P4Rv8CPsa_yJuOn9xvzyZGfQ1-WlaVuIsRL5uToHvCDgG1ltSiwggiIbmqZ4PWXA": "GG River",
    "1PvH6eX1X7UXlHuu1OXC4EaMALeHCm7OAOENuqILEvB5YNjjWQNLodHX-_lO5fuL_uGe5arFT6SKrA": "GG Gori",
    "MyWlQQPS1kht-AKuYr1yDkHLcoSDWtP-pDUzSXHbX-SPSQYY5uYWv8q7RUm-ng-1dn3G1MUjFsNDAA": "GG Stixxay",
    "A-IpujbvQPo2QAtRvAGMBQOTvrZ3gZsEjlEmYde9tySR3y58eKR-i_XjD5tBXWlvW39oRq-S76F8iA": "GG Huhi",
}

PLATFORM = cass.Platform.korea

for puuid, player in players.items():
    match_history = cass.get_match_history(
        continent=PLATFORM.continent, puuid=puuid, queue=cass.Queue.ranked_solo_fives
    )
    # Iterate through matches and store in MongoDB
    for match in match_history:
        game_id = PLATFORM.value + "_" + str(match.id)
        print(f"Processing {game_id}")

        # Check if game_id already exists
        if collection.count_documents({"game_id": game_id}) > 0:
            print(f"Game ID {game_id} already exists. Skipping.")
            continue

        bulk_data = []
        for participant in match.participants:
            if participant.summoner.puuid not in players.keys():
                continue
            # Insert participant data
            temp_data = participant.to_dict()
            temp_data["side"] = temp_data["side"].value
            participant_data = {
                "game_id": game_id,
                "player_name": player,
                "puuid": participant.summoner.puuid,
                "data_type": "PARTICIPANT",
                "data": stringify_keys(temp_data),
            }
            bulk_data.append(participant_data)

            # Insert timeline data
            for timeline_event in participant.timeline.events:
                timeline_data = {
                    "game_id": game_id,
                    "player_name": player,
                    "puuid": participant.summoner.puuid,
                    "data_type": "TIMELINE",
                    "data": stringify_keys(timeline_event.to_dict()),
                }
                bulk_data.append(timeline_data)
        # Insert data in bulk for the current match
        if bulk_data:
            collection.insert_many(bulk_data)
            bulk_data.clear()
