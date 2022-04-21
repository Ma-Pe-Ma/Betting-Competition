app_secure_key = "dev"

user_invitation_key = "registration"
admin_invitation_key = "admin"

from dateutil import tz
local_zone = tz.gettz('Europe/Budapest')

# times in UTC!!!!
#the start time of the first match
group_deadline_time = "2022-11-21 10:00"
#30 minutes after the last group stage match is finished
group_evaluation_time = "2022-12-02 19:00"

#the match time with and without extra time (after this time the csv will be updated) [hours]
match_base_time = 2
match_extra_time = 2.5

starting_bet_amount = 2000
max_group_bet_value = 50
max_final_bet_value = 200
default_max_bet_per_match = 50

#language identifier only used for emailresource identifying
language = 'hu'

#TODO ezt itt kiszedni
invalid_bet_amount = "Invalid bet amount"
invalid_goal_value = "Invalid goal value"