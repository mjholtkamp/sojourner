import datetime
import email
import os
import logging
import re
from imaplib import IMAP4_SSL

from conf import constants, settings


logger = logging.getLogger()

CHECK_METHODS = ('dkim', 'spf', 'dmarc')


def enrich_settings_from_env(settings):
    params = ('IMAP_USERNAME', 'IMAP_PASSWORD')
    for param in params:
        setattr(settings, param, os.environ.get(param, getattr(settings, param)))


def failed_methods(from_address, auth_results):
    methods = set()
    for header in auth_results:
        authserv_id, results = header.split(';', 1)
        check_methods = '|'.join(CHECK_METHODS)
        pattern = f'({check_methods})=fail'
        for method in re.findall(pattern, results):
            methods.add(method)

    return methods


def headers_summary(message):
    summary = 'From: {sender}, Subject: {subject}'
    return summary.format(sender=message['From'], subject=message['Subject'])


def main():
    enrich_settings_from_env(settings)

    current_date_time = datetime.datetime.utcnow()

    with IMAP4_SSL(host=settings.IMAP_HOSTNAME) as imap:
        imap.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        imap.select(settings.IMAP_LIST_FOLDER)
        rc, msgnums = imap.uid('search', None, 'UNSEEN')
        if rc != 'OK':
            raise Exception(f'Unexpected response while searching: {rc}')

        auth_results = {}
        for msgnum in msgnums[0].split():
            rc, mail_data = imap.uid('fetch', msgnum, '(BODY[HEADER])')
            if rc != 'OK':
                raise Exception(f'Unexpected response while fetching message {msgnum}: {rc}')

            message = email.message_from_bytes(mail_data[0][1])
            if constants.HEADER_DATE_TIME not in message:
                logger.info(f'Ignoring (no header): {headers_summary(message)}')
                continue

            sent_date_time = datetime.datetime.fromisoformat(message[constants.HEADER_DATE_TIME])
            delta = current_date_time - sent_date_time
            if delta > datetime.timedelta(seconds=settings.CHECK_ACCEPT_AGE_SECONDS):
                logger.info(f'Ignoring (too old): {headers_summary(message)}')
                continue

            auth_results[message['From']] = message.get_all('Authentication-Results')

        addresses_succeeded = 0
        for expected_address in settings.SMTP_FROM_ADDRESSES:
            if expected_address not in auth_results:
                logger.error(f'Did not find {expected_address} in emails, did something go wrong there?')
                continue

            methods = failed_methods(expected_address, auth_results[expected_address])
            if methods:
                logger.error(f'{expected_address} failed methods: {methods}')

            addresses_succeeded += 1
        
        # only if there were no problems, if there were problems, we leave emails for debugging
        if addresses_succeeded == len(settings.SMTP_FROM_ADDRESSES):
            for msgnum in msgnums[0].split():
                imap.uid('store', msgnum, '+FLAGS', '\\Deleted')
            imap.expunge()

main()