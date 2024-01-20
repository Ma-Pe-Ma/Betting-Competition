from app.notification.notifier import Notifier
from app.notification.gmail_notifier import GmailNotifier
from app.notification.browser_notifier import BrowserNotifier

from flask import current_app

notifier : Notifier = None

def init_notifier(app):
    notification_map = {
        0 : Notifier,
        1 : GmailNotifier,
        2 : BrowserNotifier
    }

    global notifier
    notifier = notification_map[app.config['DIRECT_MESSAGING']]()
