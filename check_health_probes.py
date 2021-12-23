import argparse
import datetime
import email
import logging
import os
import re
from email.message import Message
from imaplib import IMAP4, IMAP4_SSL
from types import ModuleType
from collections.abc import Sequence

from conf import constants, settings

logger = logging.getLogger()

CHECK_METHODS = ('dkim', 'spf', 'dmarc')

AuthHeaders = list[str]
AuthResults = dict[str, AuthHeaders]


def enrich_settings_from_env(settings: ModuleType) -> None:
    params = ('IMAP_USERNAME', 'IMAP_PASSWORD')
    for param in params:
        setattr(settings, param, os.environ.get(param, getattr(settings, param)))


def failed_methods(from_address: str, auth_headers: AuthHeaders) -> set[str]:
    methods: set[str] = set()
    for header in auth_headers:
        _, results = header.split(';', 1)
        check_methods = '|'.join(CHECK_METHODS)
        pattern = f'({check_methods})=(?!pass)'
        for method in re.findall(pattern, results):
            methods.add(method)

    return methods


def headers_summary(message: Message) -> str:
    summary = 'From: {sender}, Subject: {subject}'
    return summary.format(sender=message['From'], subject=message['Subject'])


def imap_recent_health_messages(imap: IMAP4, current_date_time: datetime.datetime) -> tuple[list[Message], list[str]]:
    rc, msgnums = imap.uid('search', '', 'UNSEEN')
    if rc != 'OK':
        raise Exception(f'Unexpected response while searching: {rc}')

    messages: list[Message] = []
    uids = msgnums[0].split()
    for uid in uids:
        rc, mail_data = imap.uid('fetch', uid, '(BODY[HEADER])')
        if rc != 'OK':
            raise Exception(f'Unexpected response while fetching message {uid}: {rc}')

        message = email.message_from_bytes(mail_data[0][1])
        if constants.HEADER_DATE_TIME not in message:
            logger.info(f'Ignoring (no header): {headers_summary(message)}')
            continue

        sent_date_time = datetime.datetime.fromisoformat(message[constants.HEADER_DATE_TIME])
        delta = current_date_time - sent_date_time
        if delta > datetime.timedelta(seconds=settings.CHECK_ACCEPT_AGE_SECONDS):
            logger.info(f'Ignoring (too old): {headers_summary(message)}')
            continue

        messages.append(message)

    return messages, uids


def auth_results(messages: list[Message]) -> AuthResults:
    headers: AuthResults = {}
    for message in messages:
        headers[message['From']] = message.get_all('Authentication-Results')

    return headers


def log_failed_messages(auth_results: AuthResults, addresses: Sequence[str]) -> int:
    address_failed = len(addresses)
    for expected_address in addresses:
        if expected_address not in auth_results:
            logger.error(f'Did not find {expected_address} in emails, did something go wrong there?')
            continue

        methods = failed_methods(expected_address, auth_results[expected_address])
        if methods:
            logger.error(f'{expected_address} failed methods: {", ".join(methods)}')
            headers = '\n'.join(auth_results[expected_address])
            logger.error(f'Headers:\n{headers}')
            continue

        address_failed -= 1

    return address_failed


def setup_logging(args: argparse.Namespace):
    level = logging.WARNING
    if args.verbose:
        level = logging.DEBUG

    logging.basicConfig(format='%(asctime)s %(levelname)8s: %(message)s', level=level)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()

    setup_logging(args)
    enrich_settings_from_env(settings)

    current_date_time = datetime.datetime.utcnow()

    with IMAP4_SSL(host=settings.IMAP_HOSTNAME) as imap:
        imap.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        imap.select(settings.IMAP_LIST_FOLDER)
        messages, uids = imap_recent_health_messages(imap, current_date_time)
        addresses_failed = log_failed_messages(auth_results(messages), settings.SMTP_FROM_ADDRESSES)

        # If there were problems, we leave emails for debugging, otherwise we delete the successful ones
        if not addresses_failed:
            for uid in uids:
                imap.uid('store', uid, '+FLAGS', '\\Deleted')
            imap.expunge()


main()
