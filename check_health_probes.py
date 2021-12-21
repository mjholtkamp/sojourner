import os
import email
import logging
import re
from imaplib import IMAP4_SSL

from conf import settings


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


def main():
    enrich_settings_from_env(settings)

    with IMAP4_SSL(host=settings.IMAP_HOSTNAME) as imap:
        imap.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        imap.select(settings.IMAP_LIST_FOLDER)
        rc, msgnums = imap.search(None, 'ALL')
        if rc != 'OK':
            raise Exception(f'Unexpected response while searching: {rc}')

        auth_results = {}
        for msgnum in msgnums[0].split():
            rc, mail_data = imap.fetch(msgnum, '(BODY[HEADER])')
            if rc != 'OK':
                raise Exception(f'Unexpected response while fetching message {msgnum}: {rc}')

            message = email.message_from_bytes(mail_data[0][1])
            auth_results[message['From']] = message.get_all('Authentication-Results')

    for expected_address in settings.SMTP_FROM_ADDRESSES:
        if expected_address not in auth_results:
            logger.error(f'Did not find {expected_address} in emails, did something go wrong there?')
            continue

        methods = failed_methods(expected_address, auth_results[expected_address])
        if methods:
            logger.error(f'{expected_address} failed methods: {methods}')

main()