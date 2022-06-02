#!/bin/bash
export app_secret_key="dev"

export DATABASE_URL="dbname=flask_db user=flask password=bet host=localhost"

export MATCH_URL="https://path.com/fixture"

export session_timeout=30

export user_invitation_key="registration"
export admin_invitation_key="admin"

export local_zone="Europe/Budapest"

export register_deadline_time="2022-11-21 11:00"
export group_deadline_time="2022-11-21 10:00"
export group_evaluation_time="2022-12-02 19:00"

export match_base_time=2
export match_extra_time=2.5

export starting_bet_amount=2000
export max_group_bet_value=50
export max_final_bet_value=200
export default_max_bet_per_match=50

export resource_language="hu"

export REMARK42_URL="https://remarkhost.com:8080"
export REMARK42_SITE_ID="remark"