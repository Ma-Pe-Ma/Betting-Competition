from datetime import datetime

# method use to order groups by their ID
def order_groups(group):
    return group.ID

# method use to order groups by their position
def order_teams(team):
    return team.position

# ordering days by date
def order_date(day):
    return datetime.strptime(day.date, "%Y-%m-%d")

# ordering matches on a day by starting time
def order_time(match):
    return datetime.strptime(match.time, "%H:%M")

def order_matches2(match):
    return datetime.strptime(match["time"], "%Y-%m-%d %H:%M")

# ordering groupt results
def order_group_results(group_result):
    return group_result["position"]

# ordering current player standings
def order_current_player_standings(current_player_standing):
    return current_player_standing.point