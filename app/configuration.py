import os
from dateutil import tz

DATABASE_URL = os.environ['DATABASE_URL']
REMARK42_URL = os.environ['REMARK42_URL']
REMARK42_SITE_ID = os.environ['REMARK42_SITE_ID']

app_secure_key = os.environ['app_secure_key']

# in minutes!
session_timeout = int(os.environ['session_timeout'])

user_invitation_key = os.environ['user_invitation_key']
admin_invitation_key = os.environ['admin_invitation_key']

local_zone = tz.gettz(os.environ['local_zone'])

# times in UTC!!!!
#the start time of the first match, format: '%Y-%m-%d %H:%M'
group_deadline_time = os.environ['group_deadline_time']
#30 minutes after the last group stage match is finished, format: '%Y-%m-%d %H:%M'
group_evaluation_time = os.environ['group_evaluation_time']

#the match time with and without extra time (after this time the csv will be updated) [hours], format: float
match_base_time = float(os.environ['match_base_time'])
match_extra_time = float(os.environ['match_extra_time'])

#values for configuring betting values, format: int
starting_bet_amount = int(os.environ['starting_bet_amount'])
max_group_bet_value = int(os.environ['max_group_bet_value'])
max_final_bet_value = int(os.environ['max_final_bet_value'])
default_max_bet_per_match = int(os.environ['default_max_bet_per_match'])

#language identifier only used for emailresource identifying
resource_language = os.environ['resource_language']

#TODO remove this
invalid_bet_amount = "Invalid bet amount"
invalid_goal_value = "Invalid goal value"