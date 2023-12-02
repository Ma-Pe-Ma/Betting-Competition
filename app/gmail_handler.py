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
from google.oauth2 import service_account
import json

import xml.etree.ElementTree as ET

import base64
import mimetypes
import os.path

from flask import current_app, g

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_email_resource_by_tag(tag):
    with current_app.open_resource('./templates/email-messages.xml', 'r') as email_file:
        tree = ET.ElementTree(ET.fromstring(email_file.read()))
        root = tree.getroot()

        for item in root:
            if item.tag == tag:
                for sub_item in item:
                    if sub_item.tag == 'Subject':
                        subject = sub_item.text
                    elif sub_item.tag == 'Content':
                        content = sub_item.text

                return (subject, content)

def get_credentials():
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    # version 1: if token file used
    if os.path.exists('token.json'):
       creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # version 2: this variable holds the content of the token.json, and saved on heroku dash
    # with this you can use gmail api on heroku but token needs to be generated firstly
    # Token generation is currently made manually, see below
    # quite complicated to automatize it (not worth it) https://developers.google.com/identity/protocols/oauth2/web-server#python_1
    #if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') is not None:
    #    json_str = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    #    json_data = json.loads(json_str)
    #    creds = Credentials.from_authorized_user_info(info=json_data, scopes=SCOPES)
    
    # only used to create token.json at the first time, both version 1-2 needs it
    # but version 2 cant be run on heroku, needs to be run first locally
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

    # version3 - service account info sign in for servers, requires only key, but only works with google workspace accounts
    # not suitable for our case
    '''json_str = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    json_data = json.loads(json_str)
    json_data['private_key'] = json_data['private_key'].replace('\\n', '\n')

    creds = service_account.Credentials.from_service_account_info(json_data, scopes=SCOPES)'''

    return creds

def create_message(sender, to, subject, message_text, subtype = 'plain'):
    message = MIMEText(message_text, subtype)
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

def create_draft(service, user_id, message):
    try:
        message = {'message' : message}
        draft = service.users().drafts().create(userId=user_id, body=message).execute()

        return draft

    except HttpError as error:
        print(f'An error occurred while creating drafts: {error}')

def create_drafts(drafts):
    if os.environ.get('email_sending') == 'True':
        creds = get_credentials()
    else:
        print(str(len(drafts)) + ' drafts were not created as sending is disabled.')
        return

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        for draft in drafts:
            create_draft(service=service, user_id='me', message_body=draft)

    except HttpError as error:
        print(f'An error occurred while sending messages: {error}')

def send_message(service, user_id, message):
    try:
        service.users().messages().send(userId=user_id, body=message).execute()

        return message
    except HttpError as error:
        print('An error occurred while sending a message: %s' % error)

def send_messages(messages):
    if os.environ.get('email_sending') == 'True':
        creds = get_credentials()
    else:
        print(str(len(messages)) + ' messages were not sent as sending is disabled.')
        return

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        for message in messages: 
            # create_draft(service=service, user_id='me', message=message)
            send_message(service=service, user_id='me', message=message)

    except HttpError as error:
        print(f'An error occurred while sending messages: {error}')