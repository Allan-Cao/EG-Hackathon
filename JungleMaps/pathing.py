# Based on https://github.com/James-Woodland/JungleMaps/blob/main/Jungle%20Maps/JunglePaths.py

from collections import defaultdict
import requests as r
import pandas as pd
import os
from matplotlib import pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from adjustText import adjust_text

champions = r.get(
    "https://ddragon.leagueoflegends.com/cdn/13.20.1/data/en_US/champion.json"
).json()
champion_map = {key: champions["data"][key]["name"] for key in champions["data"].keys()}


def MSConverter(milliseconds):
    seconds = round(milliseconds / 1000)
    minutes = str(seconds // 60).zfill(2)
    seconds = str(seconds - ((seconds // 60) * 60)).zfill(2)
    return minutes, seconds


def getImage(path, zoom=0.1):
    return OffsetImage(plt.imread(path), zoom=zoom)


def setup_plot(axes, img):
    axes.set_ylim(-120, 14980)
    axes.set_xlim(-120, 14870)
    plt.style.use("ggplot")
    plt.axis("off")
    plt.imshow(img, extent=[-120, 14870, -120, 14980])


gameIDs = []

campsDict = {
    "blueCamp": "Blue",
    "dragon": "Dragon",
    "gromp": "Gromp",
    "krug": "Krugs",
    "raptor": "Raptors",
    "redCamp": "Red",
    "riftHerald": "Herald",
    "scuttleCrab": "Scuttle",
    "wolf": "Wolves",
    "recall": "Recall",
}

objective_events = pd.read_parquet("objective_kills.parquet")
player_events = pd.read_parquet("snapshot_player_stats.parquet")
game_summary = pd.read_parquet("game_summary.parquet")

TEAM_TO_SCOUT = "C9"
PLAYER_TO_SCOUT = "Blaber"

AVAILABLE_GAMES = player_events[(player_events.team == TEAM_TO_SCOUT)].game_urn.unique()

player_events_sorted = player_events[
    (player_events.team == TEAM_TO_SCOUT) & (player_events.player == PLAYER_TO_SCOUT)
]
objective_events_sorted = objective_events[
    (objective_events.killer_team == TEAM_TO_SCOUT)
    & (
        (objective_events.killer == PLAYER_TO_SCOUT)
        | (
            objective_events.assistants.apply(
                lambda x: PLAYER_TO_SCOUT in x if isinstance(x, list) else False
            )
        )
    )
]

roles = ["top", "jng", "mid", "bot", "sup"]

for game_id in AVAILABLE_GAMES:
    player_event_data = player_events_sorted[(player_events_sorted.game_urn == game_id)]
    objective_kill_data = objective_events_sorted[
        (objective_events_sorted.game_urn == game_id)
    ]

    combined_df = pd.concat(
        [player_event_data, objective_kill_data],
        keys=["MAP_UPDATES", "JUNGLE"],
        axis=0,
        sort=False,
    )
    sorted_combined_df = combined_df.sort_values(by="game_time")

    game_summary_data = game_summary[(game_summary.game_urn == game_id)].iloc[0]
    is_blue = game_summary_data.team_1_name == TEAM_TO_SCOUT
    enemy_team = (
        game_summary_data.team_1_name
        if game_summary_data.team_1_name != TEAM_TO_SCOUT
        else game_summary_data.team_2_name
    )

    team_1_champions = [game_summary_data[f"team_1_{role}"] for role in roles]
    team_2_champions = [game_summary_data[f"team_2_{role}"] for role in roles]

    patch = ".".join(game_summary_data.game_version.split(".")[0:2])
    junglerChamp = champion_map[
        game_summary_data.team_1_jng if is_blue else game_summary_data.team_2_jng
    ]

    clears = 0
    recalled = True
    previousPos = (0, 0) if is_blue else (15000, 15000)
    clear_pos_data = defaultdict(list)
    camp_data = defaultdict(list)
    for (source, _), row in sorted_combined_df.iterrows():
        if source == "JUNGLE" and clears < 2:
            minutes, seconds = MSConverter(row.game_time)
            data = {
                "camp_x": row.pos_x,
                "camp_y": row.pos_y,
                "camp_type": row.monster_type,
                "game_time": row.game_time,
                "minutes": minutes,
                "seconds": seconds,
            }
            camp_data[clears].append(data)
        else:
            if row.game_time >= 90000:
                if is_blue and row.pos_x < 1500 and row.pos_y < 1500 and clears < 2:
                    recalled = True
                elif (
                    not is_blue
                    and row.pos_x > 13000
                    and row.pos_y > 13000
                    and clears < 2
                ):
                    recalled = True
                else:
                    recalled = False

                if (
                    is_blue
                    and previousPos[0] > 1500
                    and previousPos[1] > 1500
                    and row.pos_x < 1500
                    and row.pos_y < 1500
                ) or (
                    not is_blue
                    and previousPos[0] < 13000
                    and previousPos[1] < 13000
                    and row.pos_x > 13000
                    and row.pos_y > 13000
                ):
                    minutes, seconds = MSConverter(row.game_time)
                    data = {
                        "camp_x": previousPos[0],
                        "camp_y": previousPos[1],
                        "camp_type": "recall",
                        "game_time": row.game_time,
                        "minutes": minutes,
                        "seconds": seconds,
                    }
                    camp_data[clears].append(data)
                    clears += 1

                if recalled == False and clears < 2:
                    clear_pos_data[clears].append((row.game_time, row.pos_x, row.pos_y))

                previousPos = (row.pos_x, row.pos_y)

    disk_path = f"paths/{TEAM_TO_SCOUT}/{game_id.split(':')[-1]}"
    os.makedirs(disk_path, exist_ok=True)

    position_data = defaultdict(list)

    def plot_camps_and_text(clear_number, axes, position_data, Bbox):
        for i, taken_camp in enumerate(camp_data[clear_number]):
            x, y = taken_camp["camp_x"], taken_camp["camp_y"]
            position_data[clear_number].append((x, y))

            text_x = -4500
            text_y = 9000 - (i * 1000)

            axes.text(
                text_x,
                text_y,
                f"{taken_camp['minutes']}:{taken_camp['seconds']} {campsDict[taken_camp['camp_type']]}",
                fontsize=14,
            )

            path = f"Icons/{taken_camp['camp_type']}.png"
            ab = AnnotationBbox(getImage(path), (x, y), frameon=False)
            Bbox.append(ab)

            camp_data[clear_number][i] = axes.text(
                taken_camp["camp_x"],
                taken_camp["camp_y"],
                f"{taken_camp['minutes']}:{taken_camp['seconds']}",
                color="red",
                ha="center",
                va="center",
                zorder=100,
                fontsize=10,
                weight="bold",
            )

    for clear_number in range(2):
        fig, axes = plt.subplots(figsize=(12, 7))
        img = plt.imread("map11.png")
        setup_plot(axes, img)

        plt.title(
            f"{TEAM_TO_SCOUT} vs {enemy_team} - Clear {clear_number + 1}",
            fontsize=14,
            y=1.02,
            loc="left",
        )

        plt.plot(
            [coord[1] for coord in clear_pos_data[clear_number]],
            [coord[2] for coord in clear_pos_data[clear_number]],
        )

        Bbox = []
        plot_camps_and_text(clear_number, axes, position_data, Bbox)

        for ab in Bbox:
            axes.add_artist(ab)

        im = plt.imread(f"champion_images/{junglerChamp}.png")
        newax = fig.add_axes([0.05, 0.68, 0.2, 0.2], anchor="NW", zorder=-1)
        newax.imshow(im)
        newax.axis("off")

        # Constants for position and size
        CHAMPION_IMG_SIZE = 0.1
        INITIAL_VERTICAL_POSITION_C9 = 0.85
        INITIAL_VERTICAL_POSITION_EG = 0.85
        ALLIED_HOR_POS = 0.75
        ENEMY_HOR_POS = 0.85
        VS_TEXT_VERTICAL_POSITION = (
            INITIAL_VERTICAL_POSITION_C9 + INITIAL_VERTICAL_POSITION_EG
        ) / 2

        # Load and position C9 champions
        for idx, champ_name in enumerate(team_1_champions):
            im = plt.imread(f"champion_images/{champion_map[champ_name]}.png")
            newax = fig.add_axes(
                [
                    ALLIED_HOR_POS,
                    INITIAL_VERTICAL_POSITION_C9 - idx * CHAMPION_IMG_SIZE,
                    CHAMPION_IMG_SIZE,
                    CHAMPION_IMG_SIZE,
                ],
                anchor="NW",
                zorder=-1,
            )
            plt.text(
                ALLIED_HOR_POS + 0.075,
                INITIAL_VERTICAL_POSITION_C9 - idx * CHAMPION_IMG_SIZE + 0.05,
                "vs",
                fontsize=14,
                ha="center",
                va="center",
                transform=plt.gcf().transFigure,
            )
            newax.imshow(im)
            newax.axis("off")

        # Load and position EG champions
        for idx, champ_name in enumerate(team_2_champions):
            im = plt.imread(f"champion_images/{champion_map[champ_name]}.png")
            newax = fig.add_axes(
                [
                    ENEMY_HOR_POS,
                    INITIAL_VERTICAL_POSITION_EG - idx * CHAMPION_IMG_SIZE,
                    CHAMPION_IMG_SIZE,
                    CHAMPION_IMG_SIZE,
                ],
                anchor="NW",
                zorder=-1,
            )
            newax.imshow(im)
            newax.axis("off")

        adjust_text(
            camp_data[clear_number],
            [_[0] for _ in position_data[clear_number]],
            [_[1] for _ in position_data[clear_number]],
            Bbox,
            ax=axes,
            force_points=(5, 5),
            horizontalalignment="center",
            arrowprops=dict(
                shrinkB=5,
                arrowstyle="->",
                color="red",
                lw=1.5,
                relpos=(0.5, 0.5),
            ),
        )

        plt.savefig(f"{disk_path}/clear{clear_number + 1}.png")

        plt.clf()
