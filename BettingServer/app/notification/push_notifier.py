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

        # angular pwa needs the message format like this
        data = {
            'notification': {
                'title' : subject,
                'body' : message_text,
                'icon' : '/ball.svg',
                "data": {
                    'onActionClick': {
                        'default': {
                            'operation': 'openWindow',
                            'url': '/'
                        }
                    }
                }
            }
        }

        message = {
            'endpoints' : [endpoint.client_data for endpoint in endpoints.fetchall()],
            'data' : data,
            'user' : user
        }

        return message

    def send_messages(self, messages):
        sent = []
        not_sent = []

        for message in messages:
            for endpoint in message['endpoints']:
                try:
                    webpush(
                        json.loads(endpoint),
                        json.dumps(message['data']),
                        vapid_private_key=current_app.config['PUSH_KEYS']['private'],
                        vapid_claims={'sub' : current_app.config['PUSH_KEYS']['email']}
                    )

                    sent.append(message['user'])

                except WebPushException as ex:
                    not_sent.append({'user' : message['user'], 'code': ex.response.status_code})

                    if ex.response.status_code < 200 or 299 < ex.response.status_code: 
                        qs = text('DELETE FROM push_notification WHERE client_data=:c')
                        get_db().session.execute(qs, {'c' : endpoint})
                        get_db().session.commit()

        return {'sent' : sent, 'not_sent': not_sent}
