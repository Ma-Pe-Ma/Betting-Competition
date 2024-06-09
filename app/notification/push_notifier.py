from flask import g
from flask import current_app

from sqlalchemy import text
from pywebpush import webpush, WebPushException

import json

from app.notification.notifier import Notifier
from app.tools.db_handler import get_db

class PushNotifier(Notifier):
    def __init__(self):
        super(Notifier, self).__init__()

    def get_notification_resource_by_tag(self, tag):
        with current_app.open_resource('./templates/notifications/{tag}-push.html'.format(tag=tag), 'r') as notification_message, current_app.open_resource('./templates/notifications/{tag}-subject.txt'.format(tag=tag), 'r') as notification_subject:
            return (notification_subject.read(), notification_message.read())

    def create_message(self, sender, user, subject, message_text, subtype = 'plain'):
        query_string = text('SELECT client_data FROM push_notification WHERE username=:u')
        endpoints = get_db().session.execute(query_string, {'u' : user['username']})

        data = {
            'title' : subject,
            'options' : {
                'body' : message_text,
                'icon' : '/static/ball.svg',
                'badge': '/static/ball.svg'
            }
        }

        message = {
            'endpoints' : [endpoint.client_data for endpoint in endpoints.fetchall()],
            'data' : data
        }

        return message

    def send_messages(self, messages):
        for message in messages:
            for endpoint in message['endpoints']:
                try:
                    webpush(
                        json.loads(endpoint),
                        json.dumps(message['data']),
                        vapid_private_key=current_app.config['PUSH_KEYS']['private'],
                        vapid_claims={'sub' : current_app.config['PUSH_KEYS']['email']}
                    )
                except WebPushException as ex:
                    if ex.response.status_code < 200 or 299 < ex.response.status_code: 
                        qs = text('DELETE FROM push_notification WHERE client_data=:c')
                        get_db().session.execute(qs, {'c' : endpoint})
                        get_db().session.commit()
