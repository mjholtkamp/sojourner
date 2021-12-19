import os
from smtplib import SMTP_SSL
from email.message import EmailMessage

from conf import settings


def enrich_settings_from_env(settings):
    params = ('SMTP_USERNAME', 'SMTP_PASSWORD')
    for param in params:
        setattr(settings, param, os.environ.get(param, getattr(settings, param)))


def main():
    enrich_settings_from_env(settings)
    msg = EmailMessage()
    msg['Subject'] = 'Health check'
    msg['From'] = settings.SMTP_FROM
    msg['To'] = settings.SMTP_TO
    msg.set_content('Health check email')
    with SMTP_SSL(host=settings.SMTP_HOST, port=settings.SMTP_PORT) as smtp:
        smtp.set_debuglevel(settings.SMTP_DEBUG)
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(msg)

main()