from app.notification.notifier import Notifier

notifier : Notifier = None
notifier_type = None

def init_notifier(app):
    global notifier_type
    notifier_type = app.config['DIRECT_MESSAGING']

def get_notifier():
    global notifier

    if notifier == None:
        from app.notification.gmail_notifier import GmailNotifier
        # importing needs to happen here as pywebpush can't work if it's created at init and when it's forked with gunicorn's --preload flag
        from app.notification.push_notifier import PushNotifier

        notification_map = {
            0 : Notifier,
            1 : GmailNotifier,
            2 : PushNotifier
        }

        global notifier_type
        notifier = notification_map[notifier_type]()

    return notifier