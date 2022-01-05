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
group_evaluation_time = "2021-12-10 19:00"

#the match time with and without extra time (after this time the csv will be updated)
match_base_time = 2
match_extra_time = 2.5

starting_bet_amount = 2000
max_group_bet_value = 50
max_final_bet_value = 200

#TODO ezt itt kiszedni
invalid_bet_amount = "Invalid bet amount"
invalid_goal_value = "Invalid goal value"