from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.configuration import language
import xml.etree.ElementTree as ET

import base64
import mimetypes
import os.path

from flask import current_app

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_email_resource_by_tag(tag):    
    with current_app.open_resource("./templates/email-messages.xml", 'r') as email_file:
        tree = ET.ElementTree(ET.fromstring(email_file.read()))
        root = tree.getroot()

        for item in root:
            if item.tag == 'Collection':
                if item.attrib['lan'] == language:
                    for res in item:
                        if res.tag == tag:
                            for sub_item in res:
                                if sub_item.tag == 'Subject':
                                    subject = sub_item.text
                                elif sub_item.tag == 'Content':
                                    content = sub_item.text

                            email_object = (subject, content)

                            return email_object

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def create_message_with_attachment(sender, to, subject, message_text, file):
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    content_type, encoding = mimetypes.guess_type(file)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(file, 'rb')
            msg = MIMEText(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(file, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(file, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(file, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(file)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def create_draft(message_body):
    creds = get_credentials()

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        
        message = {'message' : message_body}

        draft = service.users().drafts().create(userId='me', body = message).execute()

        #print('Draft id: %s\nDraft message: %s' % draft['id'], draft['message'])

        return draft

    except HttpError as error:
        print(f'An error occurred while creating drafts: {error}')

def send_message(service, user_id, message):
    try:
        service.users().messages().send(userId=user_id, body=message.execute())

        return message
    except HttpError as error:
        print('An error occurred while sending a message: %s' % error)

def send_messages(messages):
    creds = get_credentials()

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        for message in messages:
            send_message(service=service, user_id='me', message=message)

    except HttpError as error:
        print(f'An error occurred while sending messages: {error}')