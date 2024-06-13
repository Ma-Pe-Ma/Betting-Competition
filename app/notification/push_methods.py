from flask import Blueprint
from flask import request
from flask import g
from flask import send_file
from flask import render_template_string
from flask import current_app

from app.auth import sign_in_required
from app.tools.db_handler import get_db
from app.notification.notification_handler import get_notifier

from sqlalchemy import text

bp = Blueprint('notification', __name__, '''url_prefix="/notification"''')

@bp.route('/sw.js')
def service_worker():
    return send_file('./static/js/service_worker.js')

@bp.route('/notification/subscribe', methods=['POST'])
@sign_in_required()
def subscribe():
    try:
        query_string = text('INSERT INTO push_notification (username, client_data) VALUES (:u, :c)')

        get_db().session.execute(query_string, {'u' : g.user['username'], 'c' : request.get_data().decode('utf-8')})
        get_db().session.commit()

        user = {'username' : g.user['username']}

        notifier = get_notifier()
        welcome = notifier.get_notification_resource_by_tag('welcome')

        messages = [notifier.create_message(sender='me', user=user, subject=render_template_string(welcome[0]), message_text=render_template_string(welcome[1]))]
        notifier.send_messages(messages)
    except Exception as error:
        current_app.logger.info('Failed to subscribe for push notification: ' + str(error))
        return '', 400

    return ''
