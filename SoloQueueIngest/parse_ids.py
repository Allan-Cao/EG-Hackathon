import cassiopeia as cass
from dotenv import load_dotenv
import os

# Initialize env variables
load_dotenv()
API_KEY = os.getenv('RIOT_API')

cass.set_riot_api_key(API_KEY)

player_account_mapping = {}
with open("KR Bootcamp IDs.txt", "r", encoding="utf-8") as f:
    for line in f:
        # Skip empty lines
        if line.strip() == "":
            continue

        player, account = map(str.strip, line.split('-', 1))
        player_account_mapping[cass.get_summoner(name=account, region="KR").puuid] = player

print(player_account_mapping)
