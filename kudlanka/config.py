# a hack to enable mounting the app at an arbitrary URL prefix
KROOT = ""


def k(url):
    return KROOT + url


# Flask Security config
SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
SECURITY_LOGIN_URL = k("/login")
SECURITY_LOGOUT_URL = k("/logout")
SECURITY_POST_LOGIN_VIEW = k("/")
SECURITY_POST_LOGOUT_VIEW = k("/")

# register users manually using mongo shell (see README)
# SECURITY_SEND_REGISTER_EMAIL = False
# SECURITY_REGISTERABLE = True
# SECURITY_REGISTER_URL = k("/register")
# SECURITY_POST_REGISTER_VIEW = k("/edit")

# MongoDB config
MONGODB_DB = "ktest"
MONGODB_HOST = "localhost"
MONGODB_PORT = 27017

# only useful for keeping track of sessions in production; comment out when
# running on localhost, because SERVER_NAME needs to be a fully qualified
# domain name in order for sessions to work
# SERVER_NAME = "trnka.korpus.cz:5000"
# APPLICATION_ROOT = "/"

MAX_DISAMB_PASSES = 2
