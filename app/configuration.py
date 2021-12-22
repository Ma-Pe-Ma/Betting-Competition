app_secure_key = "dev"

user_invitation_key = "registration"
admin_invitation_key = "admin"

from dateutil import tz
local_zone = tz.gettz('Europe/Budapest')

day_names = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]

# times in UTC!!!!
#the start time of the first match
group_deadline_time = "2021-12-10 18:00"
#30 minutes after the last group stage match is finished
group_evaluation_date = "2021-12-10 12:00"

starting_bet_amount = 2000
max_group_bet_value = 50
max_final_bet_value = 200

#TODO ezt itt kiszedni
invalid_bet_amount = "Invalid bet amount"
invalid_goal_value = "Invalid goal value"