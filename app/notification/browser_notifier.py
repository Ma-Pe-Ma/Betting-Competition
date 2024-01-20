from app.notification.notifier import Notifier

class BrowserNotifier(Notifier):
    def __init__(self):
        super(Notifier, self).__init__()

    def create_message(self, sender, to, subject, message_text, subtype = 'plain'):
        pass

    def send_messages(self, messages):
        pass