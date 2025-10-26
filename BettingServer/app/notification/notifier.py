from flask import current_app

class Notifier:
    def __init__(self):
        pass

    def get_notification_resource_by_tag(self, tag):
        with current_app.open_resource('./templates/notifications/{tag}.html'.format(tag=tag), 'r') as notification_message, current_app.open_resource('./templates/notifications/{tag}-subject.txt'.format(tag=tag), 'r') as notification_subject:
            return (notification_subject.read(), notification_message.read())
                
    def create_message(self, sender, user, subject, message_text, subtype = 'plain'):
        return (sender, user, subject, message_text, subtype)

    def send_messages(self, messages):
        current_app.logger.info('Notification sending turned off: ' + str(messages))
