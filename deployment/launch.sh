#!/bin/sh

echo "Starting nginx server."
nginx -c /BettingApp/nginx.conf
echo "Starting gunicorn server."
python -m gunicorn -w 3 --max-requests 1000 --worker-class gevent --name=betting_competition --bind unix:/BettingApp/gunicorn.socket 'app:create_app(instance_path="/BettingInstance/")'
