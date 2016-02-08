from flask.ext.babel import lazy_gettext as _

# a hack to enable mounting the app at an arbitrary URL prefix
KROOT = ""


def k(url):
    return KROOT + url


# MongoDB config
MONGODB_DB = "ktest"
MONGODB_HOST = "localhost"
MONGODB_PORT = 27017

# only useful for keeping track of sessions in production; comment out when
# running on localhost, because SERVER_NAME needs to be a fully qualified
# domain name in order for sessions to work
# SERVER_NAME = "trnka.korpus.cz:5000"
# APPLICATION_ROOT = "/"

LANGUAGES = dict(en=_("English"), cs=_("Czech"))

# how many users should rate each segment
MAX_DISAMB_PASSES = 2

# GitHub repo agains which app versions should be linked to in views and issues
# reported
GITHUB = "https://github.com/dlukes/kudlanka"

# Flask Security config
SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
SECURITY_LOGIN_URL = k("/login")
SECURITY_LOGOUT_URL = k("/logout")
SECURITY_POST_LOGIN_VIEW = k("/")
SECURITY_POST_LOGOUT_VIEW = k("/")
SECURITY_CHANGEABLE = True
SECURITY_POST_CHANGE_VIEW = k("/settings")
SECURITY_CHANGE_URL = k("/settings/passwd")

# security-related strings for i18n / l10n
SECURITY_MSG_UNAUTHORIZED = (
    _("You do not have permission to view this resource."), "error")
SECURITY_MSG_CONFIRM_REGISTRATION = (
    _("Thank you. Confirmation instructions have been sent to %(email)s."),
    "success")
SECURITY_MSG_EMAIL_CONFIRMED = (
    _("Thank you. Your email has been confirmed."), "success")
SECURITY_MSG_ALREADY_CONFIRMED = (
    _("Your email has already been confirmed."), "info")
SECURITY_MSG_INVALID_CONFIRMATION_TOKEN = (
    _("Invalid confirmation token."), "error")
SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED = (
    _("%(email)s is already associated with an account."), "error")
SECURITY_MSG_PASSWORD_MISMATCH = (
    _("Password does not match"), "error")
SECURITY_MSG_RETYPE_PASSWORD_MISMATCH = (
    _("Passwords do not match"), "error")
SECURITY_MSG_INVALID_REDIRECT = (
    _("Redirections outside the domain are forbidden"), "error")
SECURITY_MSG_PASSWORD_RESET_REQUEST = (
    _("Instructions to reset your password have been sent to %(email)s."),
    "info")
SECURITY_MSG_PASSWORD_RESET_EXPIRED = (
    _("You did not reset your password within %(within)s. New instructions "
      "have been sent to %(email)s."),
    "error"),
SECURITY_MSG_INVALID_RESET_PASSWORD_TOKEN = (
    _("Invalid reset password token."), "error")
SECURITY_MSG_CONFIRMATION_REQUIRED = (
    _("Email requires confirmation."), "error")
SECURITY_MSG_CONFIRMATION_REQUEST = (
    _("Confirmation instructions have been sent to %(email)s."), "info")
SECURITY_MSG_CONFIRMATION_EXPIRED = (
    _("You did not confirm your email within %(within)s. New instructions to "
      "confirm your email have been sent to %(email)s."),
    "error"),
SECURITY_MSG_LOGIN_EXPIRED = (
    _("You did not login within %(within)s. New instructions to login have "
      "been sent to %(email)s."),
    "error"),
SECURITY_MSG_LOGIN_EMAIL_SENT = (
    _("Instructions to login have been sent to %(email)s."), "success")
SECURITY_MSG_INVALID_LOGIN_TOKEN = (
    _("Invalid login token."), "error")
SECURITY_MSG_DISABLED_ACCOUNT = (
    _("Account is disabled."), "error")
SECURITY_MSG_EMAIL_NOT_PROVIDED = (
    _("Email not provided"), "error")
SECURITY_MSG_INVALID_EMAIL_ADDRESS = (
    _("Invalid email address"), "error")
SECURITY_MSG_PASSWORD_NOT_PROVIDED = (
    _("Password not provided"), "error")
SECURITY_MSG_PASSWORD_NOT_SET = (
    _("No password is set for this user"), "error")
SECURITY_MSG_PASSWORD_INVALID_LENGTH = (
    _("Password must be at least 6 characters"), "error")
SECURITY_MSG_USER_DOES_NOT_EXIST = (
    _("Specified user does not exist"), "error")
SECURITY_MSG_INVALID_PASSWORD = (
    _("Invalid password"), "error")
SECURITY_MSG_PASSWORDLESS_LOGIN_SUCCESSFUL = (
    _("You have successfuly logged in."), "success")
SECURITY_MSG_PASSWORD_RESET = (
    _("You successfully reset your password and you have been logged in "
      "automatically."),
    "success"),
SECURITY_MSG_PASSWORD_IS_THE_SAME = (
    _("Your new password must be different than your previous password."),
    "error")
SECURITY_MSG_PASSWORD_CHANGE = (
    _("You successfully changed your password."), "success")
SECURITY_MSG_LOGIN = (
    _("Please log in to access this page."), "info")
SECURITY_MSG_REFRESH = (
    _("Please reauthenticate to access this page."), "info")
