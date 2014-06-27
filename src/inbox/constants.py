

#Environment related constants
ENV_PRODUCTION = 'PRODUCTION'
#Staging is used for testing by replicating the same production remote env
ENV_STAGING = 'STAGING'
#Development local env
ENV_DEVELOPMENT = 'DEV'
#Automated tests local env
ENV_TESTING = 'TEST'

ENVIRONMENT_CHOICES = [
    ENV_PRODUCTION,
    ENV_STAGING,
    ENV_DEVELOPMENT,
    ENV_TESTING,
]
PAGE_SIZE = 20

EMAIL_REGEXP = "^[a-zA-Z0-9'._-]+@[a-zA-Z0-9._-]+.[a-zA-Z]{2,6}$"

OAUTH2_SCOPES = 'https://www.googleapis.com/auth/userinfo.email ' \
                'https://www.googleapis.com/auth/email.migration ' \
                'https://apps-apis.google.com/a/feeds/emailsettings/2.0/ ' \
                'https://www.googleapis.com/auth/drive'

MENU_ITEMS = [
    ('admin_index', 'Home'),
    ('settings','Settings')
]

IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
IMAP_ALL_LABEL_ES = '[Gmail]/Todos'
IMAP_ALL_LABEL_EN = '[Gmail]/All Mail'
IMAP_TRASH_LABEL_EN = '[Gmail]/Trash'
IMAP_TRASH_LABEL_ES = '[Gmail]/Papelera'

GMAIL_TRASH_KEY = '(\\HasNoChildren \\Trash)'
GMAIL_ALL_KEY = '(\\HasNoChildren \\All)'

USER_CONNECTION_LIMIT = 7
MESSAGE_BATCH_SIZE = 500

STARTED = 'STARTED'
FINISHED = 'FINISHED'
FAILED = 'FAILED'

STATUS_CHOICES = [
    STARTED,
    FINISHED,
    FAILED
]

DUPLICATED = 'DUPLICATED'
MIGRATED = 'MIGRATED'

CLEANING_STATUS_CHOICES = [
    STARTED,
    DUPLICATED,
    MIGRATED,
    FINISHED
]

ATTACHMENT_FOLDER = 'Adjuntos'

GMAIL_PROPERTIES = [
    {'\\\\Inbox': 'isInbox'},
    {'\\\\Sent': 'isSent'},
    {'\\\\Starred': 'isStarred'},
    {'\\\\Draft': 'isDraft'},
    {'\\\\Unread': 'isUnread'}
]

GMAIL_PROPERTY_NAMES = [
    '\\\\Inbox',
    '\\\\Sent',
    '\\\\Starred',
    '\\\\Draft',
    '\\\\Unread',
    '\\\\Important'
]

MAX_RETRIES = 3
MAX_CLEAN_RETRIES = 1