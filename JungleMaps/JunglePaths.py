import requests
import json
from datetime import datetime
import wget
from zipfile import ZipFile
import os
from matplotlib import pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import ffmpeg
from adjustText import adjust_text
import PIL
import urllib


def MSConverter(milliseconds):
  seconds = round(milliseconds/1000)
  minutes = str(seconds//60).zfill(2)
  seconds = str(seconds - ((seconds//60)*60)).zfill(2)
  return minutes, seconds

def getImage(path, zoom=0.1):
    return OffsetImage(plt.imread(path), zoom=zoom)


# TODO: This is a hardcoded team1 name
team = "IZIDREAM"

# r = requests.post('https://lolesports-api.bayesesports.com/v2/auth/login', json={"username": username, "password": password})

# token = r.json()


# r = requests.get('https://lolesports-api.bayesesports.com/v2/games/teams/suggestions?name={}'.format(team), headers = {"Authorization": 'Bearer {}'.format(token["accessToken"])})

# abc = r.json()

# teamCode = "live:lol:riot:team:{}".format(abc[0]["esportsId"])


# r = requests.get('https://lolesports-api.bayesesports.com/v2/games?teamName={}&tags={}&size=100'.format(team, "Lfl Summer 2023"), headers = {"Authorization": 'Bearer {}'.format(token["accessToken"])})

# abc = r.json()

gameIDs = []

campsDict = {"blueCamp": "Blue", "dragon": "Dragon", "gromp": "Gromp", "krug": "Krugs", "raptor": "Raptors", "redCamp": "Red", "riftHerald": "Herald", "scuttleCrab": "Scuttle", "wolf": "Wolves"}

data = {} # Store all gameData
filePath = "objective_kills.json"
with open(filePath) as json_data:
    data = json.load(json_data)
    for event in data:
        if event["game_urn"] not in gameIDs: # Collect unique GameIDs and append to gameIDs
            gameIDs.append(event["game_urn"]) 

# Debugging
print(gameIDs)
print(data)

for gameID in gameIDs:

    gameData = []           # This contains filtered data by the gameID
    for item in data:
        if (item["game_urn"] == gameID):
            gameData.append(item)

    x = [[],[]]
    y = [[],[]]
    campsX = [[],[]]
    campsY = [[],[]]
    camps = [[],[]]
    campsTime = [[],[]]
    deathsX = [[],[]]
    deathsY = [[],[]]
    killsX = [[],[]]
    killsY = [[],[]]
    # print(json.dumps(game, indent = 4))

    opponent = "OPPONENT" # game["teams"][0]["name"]  # TODO: Fix this and implement real opponent
    # if opponent == team:
    #   opponent = game["teams"][1]["name"]

    # r = requests.get('https://lolesports-api.bayesesports.com/v2/games/{}/download'.format(game["platformGameId"]), headers = {"Authorization": 'Bearer {}'.format(token["accessToken"])}, params = {"option": "HISTORIC_BAYES_DUMP"})
    # abc = r.json()
    # response = wget.download(r.json()["url"], "Data.zip")
    # with ZipFile("Data.zip", 'r') as zipObj:
    #     zipObj.extractall()

    junglerId = ""
    junglerChamp = ""
    clears = 0
    recalled = True
    previousPos = []
    for event in gameData:
        if event["payload"]["payload"]["action"] in ["KILLED_ANCIENT"] and event["payload"]["payload"]["payload"]["killerTeamUrn"] == teamCode and event["payload"]["payload"]["payload"]["killerUrn"] == junglerId and clears < 2:
            campsX[clears].append(event["payload"]["payload"]["payload"]["position"][0])
            campsY[clears].append(event["payload"]["payload"]["payload"]["position"][1])
            camps[clears].append(event["payload"]["payload"]["payload"]["monsterType"])
            minutes, seconds = MSConverter(event["payload"]["payload"]["payload"]["gameTime"])
            campsTime[clears].append("{}:{}".format(minutes, seconds))
        if event["payload"]["payload"]["action"] == "UPDATE":
            try:
                if event["payload"]["payload"]["payload"]["gameTime"] >= 90000:
                    if event["payload"]["payload"]["payload"]["teamOne"]["liveDataTeamUrn"] == teamCode:
                        junglerId = event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["liveDataPlayerUrn"]
                        junglerChamp = event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["championName"]
                        if previousPos == []:
                                previousPos = event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["position"]
                        if event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["position"][0] < 1500 and event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["position"][1] < 1500 and clears < 2:
                            recalled = True
                        else:
                            recalled = False
                        if previousPos[0] > 1500 and previousPos[1] > 1500 and event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["position"][0] < 1500 and event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["position"][1] < 1500:
                                clears = clears + 1
                        
                        #print(clears)
                        if recalled == False and clears < 2:
                            x[clears].append(event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["position"][0])
                            y[clears].append(event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["position"][1])                                
                        
                        previousPos = event["payload"]["payload"]["payload"]["teamOne"]["players"][1]["position"]
                    
                    else:
                        junglerId = event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["liveDataPlayerUrn"]
                        junglerChamp = event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["championName"]
                        
                        if previousPos == []:
                                previousPos = event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["position"]
                        if event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["position"][0] > 13000 and event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["position"][1] > 13000:
                            recalled = True
                        else:
                            recalled = False
                        if previousPos[0] < 13000 and previousPos[1] < 13000 and event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["position"][0] > 13000 and event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["position"][1] > 13000:
                            clears = clears + 1
                        
                        if recalled == False and clears < 2:                            
                            x[clears].append(event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["position"][0])
                            y[clears].append(event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["position"][1])
                        
                        previousPos = event["payload"]["payload"]["payload"]["teamTwo"]["players"][1]["position"]   
                        
            except Exception as e:
                #print(e)
                pass
    if os.path.exists("paths/{}/{}".format(opponent, game["startedAt"].replace(":", "-"))) == False:
        os.makedirs("paths/{}/{}".format(opponent, game["startedAt"].replace(":", "-")))
    os.remove("Data.zip")
    open("dump.json", 'w').close()
    os.remove("dump.json")
    fig, axes = plt.subplots()
    img = plt.imread("map11.png")
    axes.set_ylim(-120, 14980)
    axes.set_xlim(-120, 14870)
    plt.style.use("ggplot")
    plt.axis('off')
    graph, = plt.plot([], [])
    plt.imshow(img, extent=[-120, 14870, -120, 14980])
    plt.plot(x[0], y[0])
    Bbox = []
    for i in range(len(camps[0])):
      plt.text(-5750, 9500 - (i*1000) , "{} {}".format(campsTime[0][i], campsDict[camps[0][i]]), fontsize=14)
    for camp in range(len(camps[0])):
      path = "Icons/{}.png".format(camps[0][camp])
      ab = AnnotationBbox(getImage(path), (campsX[0][camp], campsY[0][camp]), frameon=False)
      axes.add_artist(ab)
      campsTime[0][camp] = axes.text(campsX[0][camp], campsY[0][camp], campsTime[0][camp], color = "red", ha='center', va='center', zorder = 100, fontsize = 10, weight='bold')
    for i in axes.get_children():
      if isinstance(i, AnnotationBbox):
        Bbox.append(i)
    response = wget.download("http://ddragon.leagueoflegends.com/cdn/13.17.1/img/champion/{}.png".format(junglerChamp), "champ.png")
    im = plt.imread("champ.png")
    newax = fig.add_axes([0.05, 0.68, 0.2, 0.2], anchor='NW', zorder=-1)
    newax.imshow(im)
    newax.axis('off')
    os.remove("champ.png")
    adjust_text(campsTime[0], campsX[0], campsY[0], Bbox, ax = axes, only_move={'texts':'y'}, force_text = (3,3), force_objects = (10, 10), force_points = (5,5),
                horizontalalignment="center", arrowprops=dict(shrinkA=18, shrinkB=20, arrowstyle='->', color='red', lw = 1.5), text_from_points=True)
    plt.title("1st Clear")
    plt.savefig("paths/{}/{}/clear1.png".format(opponent, game["startedAt"].replace(":", "-")))

    plt.clf()
    fig, axes = plt.subplots()
    img = plt.imread("map11.png")
    axes.set_ylim(-120, 14980)
    axes.set_xlim(-120, 14870)
    plt.style.use("ggplot")
    plt.axis('off')
    graph, = plt.plot([], [])
    plt.imshow(img, extent=[-120, 14870, -120, 14980])
    plt.plot(x[1], y[1], color = "orange")
    Bbox = []
    for i in range(len(camps[1])):
      plt.text(-5750, 9500 - (i*1000) , "{} {}".format(campsTime[1][i], campsDict[camps[1][i]]), fontsize=14)
    for camp in range(len(camps[1])):
      path = "Icons/{}.png".format(camps[1][camp])
      ab = AnnotationBbox(getImage(path), (campsX[1][camp], campsY[1][camp]), frameon=False)
      axes.add_artist(ab)
      campsTime[1][camp] = axes.text(campsX[1][camp], campsY[1][camp], campsTime[1][camp], color = "red", ha='center', va='center', zorder = 100, fontsize = 10, weight='bold')
    for i in axes.get_children():
      if isinstance(i, AnnotationBbox):
        Bbox.append(i)
    response = wget.download("http://ddragon.leagueoflegends.com/cdn/13.17.1/img/champion/{}.png".format(junglerChamp), "champ.png")
    im = plt.imread("champ.png")
    newax = fig.add_axes([0.05, 0.68, 0.2, 0.2], anchor='NW', zorder=-1)
    newax.imshow(im)
    newax.axis('off')
    os.remove("champ.png")
    adjust_text(campsTime[1], campsX[1], campsY[1], Bbox, ax = axes, only_move={'texts':'y'}, force_text = (3,3), force_objects = (10, 10), force_points = (5,5),
                horizontalalignment="center", arrowprops=dict(shrinkA=18, shrinkB=20, arrowstyle='->', color='red', lw = 1.5), text_from_points=True)
    plt.title("2nd Clear")
    
    plt.savefig("paths/{}/{}/clear2.png".format(opponent, game["startedAt"].replace(":", "-")))
        
