#!/bin/sh

echo "Creating instance folder if it does not exist."
mkdir /BettingInstance/

echo "Copy configuration file if it does not exist."
cp -n ./configuration.json /BettingInstance/

echo "Initialize db with flask if it does not exist."
python -m flask --app 'app:create_app(instance_path="/BettingInstance/")' init-db

echo "Starting gunicorn server."
python -m gunicorn -w 3 --max-requests 1000 --worker-class gevent --name=betting_competition --bind unix:/BettingInstance/gunicorn.socket 'app:create_app(instance_path="/BettingInstance/")'
