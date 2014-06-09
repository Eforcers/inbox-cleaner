

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

EMAIL_REGEXP = "^[a-zA-Z0-9'._-]+@[a-zA-Z0-9._-]+.[a-zA-Z]{2,6}$"

OAUTH2_SCOPES = 'https://www.googleapis.com/auth/userinfo.email '

MENU_ITEMS = [
    ('admin_index', 'Home'),
]

IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
IMAP_ALL_LABEL_ES = '[Gmail]/Todos'
IMAP_ALL_LABEL_EN = '[Gmail]/All Mail'
IMAP_TRASH_LABEL_EN = '[Gmail]/Trash'
IMAP_TRASH_LABEL_ES = '[Gmail]/Papelera'

GMAIL_TRASH_KEY = '(\\HasNoChildren \\Trash)'
GMAIL_ALL_KEY = '(\\HasNoChildren \\All)'

MESSAGE_BATCH_SIZE = 7

STARTED = 'STARTED'
FINISHED = 'FINISHED'
FAILED = 'FAILED'

STATUS_CHOICES = [
    STARTED,
    FINISHED,
    FAILED
]