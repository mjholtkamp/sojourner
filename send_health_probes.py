import datetime
import os
from smtplib import SMTP_SSL
from email.message import EmailMessage

from conf import constants, settings


def enrich_settings_from_env(settings):
    params = ('SMTP_USERNAME', 'SMTP_PASSWORD')
    for param in params:
        setattr(settings, param, os.environ.get(param, getattr(settings, param)))


def main():
    enrich_settings_from_env(settings)
    current_datetime = datetime.datetime.utcnow()

    with SMTP_SSL(host=settings.SMTP_HOST, port=settings.SMTP_PORT) as smtp:
        msg = EmailMessage()
        msg['Subject'] = 'Health check {}'.format(current_datetime.isoformat(timespec='minutes'))
        msg['To'] = settings.SMTP_TO_ADDRESS
        msg[constants.HEADER_DATE_TIME] = current_datetime.isoformat()
        msg.set_content('Health check email')

        smtp.set_debuglevel(settings.SMTP_DEBUG)
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        for sender in settings.SMTP_FROM_ADDRESSES:
            del msg['From']
            msg['From'] = sender
            smtp.send_message(msg)

main()