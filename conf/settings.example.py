from .defaults import *

# The SMTP hostname of our self-hosted email server
SMTP_HOST = ''

# The email addresses that you want to test. The domain name is the important part
SMTP_FROM_ADDRESSES = ('me@example.com', 'me@example.net')

# The email address of another email hoster that is configured to forward emails
# to our self-hosted email server
SMTP_TO_ADDRESS = ''

# The credentials for accessing the SMTP server.
# These two can also be set by the environment variables with the same name
SMTP_USERNAME = ''
SMTP_PASSWORD = ''

# The hostname of our self-hosted IMAP server
IMAP_HOSTNAME = ''

# The credentials for accessing the IMAP server
# These two can also be set by the environment variables with the same name
IMAP_USERNAME = ''
IMAP_PASSWORD = ''
