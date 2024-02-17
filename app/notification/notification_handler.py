from app.notification.notifier import Notifier
from app.notification.gmail_notifier import GmailNotifier
from app.notification.push_notifier import PushNotifier

from flask import current_app

notifier : Notifier = None

def init_notifier(app):
    notification_map = {
        0 : Notifier,
        1 : GmailNotifier,
        2 : PushNotifier
    }

    global notifier
    notifier = notification_map[app.config['DIRECT_MESSAGING']]()
