import pandas as pd
from collections import defaultdict

df = pd.read_parquet('game_summary.parquet')

# Initialize variables
teams_data = defaultdict(
    lambda: defaultdict(
        lambda: defaultdict(int)
    )
)
team_game_count = defaultdict(int)

# Mapping for different pick times
pick_times = {
    'blue': {1: 'B1', 4: 'B2-B3', 5: 'B2-B3', 7: 'B4-B5', 8: 'B4-B5'},
    'red': {2: 'R1-R2', 3: 'R1-R2', 6: 'R3', 9: 'R4', 10: 'R5'}
}

# Analyze pick orders
for _, row in df.iterrows():
    for side, prefix in [('blue', 'team_1'), ('red', 'team_2')]:
        team_name = row[f'{prefix}_name']
        team_game_count[team_name] += 1  # Count games for each team

        # Grouping pick times
        for role in ['top', 'jng', 'mid', 'bot', 'sup']:
            pick_num = row[f'{prefix}_{role}_pick_num']
            pick_group = pick_times[side].get(pick_num, None)

            if pick_group:
                teams_data[team_name][pick_group][role] += 1

        # Grouping phases
        for phase, pick_nums in [('phase_one', range(1, 7)), ('phase_two', range(7, 11))]:
            roles_in_phase = [role for role in ['top', 'jng', 'mid', 'bot', 'sup'] if row[f'{prefix}_{role}_pick_num'] in pick_nums]
            for role in roles_in_phase:
                teams_data[team_name][phase][role] += 1

# Calculate and print percentages
for team, pick_data in teams_data.items():
    print(f"Team: {team}")
    total_games = team_game_count[team]
    for pick_group, role_data in pick_data.items():
        percentages = {k: (v / total_games) * 100 for k, v in role_data.items()}
        print(f"  {pick_group.capitalize()} Percentages: {percentages}")

# Import required libraries
import dash
from dash import dcc, html
import plotly.express as px

# Initialize the Dash app
app = dash.Dash(__name__)

# Create a DataFrame from 'teams_data' and 'team_game_count'

# Define the layout
app.layout = html.Div([
    dcc.Dropdown(
        id='team-dropdown',
        options=[{'label': team, 'value': team} for team in team_game_count.keys()],
        value=list(team_game_count.keys())[0]
    ),
    dcc.Graph(id='pick-plot')
])

# Define the callback
@app.callback(
    Output('pick-plot', 'figure'),
    [Input('team-dropdown', 'value')]
)
def update_graph(selected_team):
    # Filter DataFrame based on the selected team
    # ...

    # Create the figure using Plotly Express
    fig = px.bar(
        filtered_df,
        x='Pick Group',
        y='Percentage',
        color='Percentage',
        title=f"Pick Order Distribution for {selected_team}"
    )
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
