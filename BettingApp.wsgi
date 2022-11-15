import os
os.environ['supported_languages'] = "en,hu"

os.environ['app_secret_key'] = "dev"

os.environ['DATABASE_URL'] = ""

os.environ['MATCH_URL'] = ""

os.environ['email_sending'] = 'False'
os.environ['session_timeout'] = '15'

os.environ['user_invitation_key'] = "registration"
os.environ['admin_invitation_key'] = "admin"

os.environ['local_zone'] = "Europe/Budapest"

os.environ['register_deadline_time'] = "2022-11-20 23:59"
os.environ['group_deadline_time'] = "2022-11-20 23:59"
os.environ['group_evaluation_time'] = "2022-12-02 19:00"

os.environ['match_base_time'] = '2'
os.environ['match_extra_time'] = '2.5'

os.environ['starting_bet_amount'] = '2000'
os.environ['max_group_bet_value'] = '50'
os.environ['max_final_bet_value'] = '200'
os.environ['default_max_bet_per_match'] = '50'

from app import create_app
application = create_app()