from flask import Flask


# a hack to enable mounting the app at an arbitrary URL prefix
def k(url):
    return url


app = Flask(__name__, static_url_path = k("/static"))

# Flask Security config
app.config["SECRET_KEY"] = "foobarbaz"
app.config["SECURITY_PASSWORD_HASH"] = "pbkdf2_sha512"
app.config["SECURITY_PASSWORD_SALT"] = "foobarbaz"
app.config["SECURITY_LOGIN_URL"] = k("/login")
app.config["SECURITY_LOGOUT_URL"] = k("/logout")
app.config["SECURITY_POST_LOGIN_VIEW"] = k("/edit")
app.config["SECURITY_POST_LOGOUT_VIEW"] = k("/")

# register users manually using mongo shell (see README)
# app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
# app.config["SECURITY_REGISTERABLE"] = True
# app.config["SECURITY_REGISTER_URL"] = k("/register")
# app.config["SECURITY_POST_REGISTER_VIEW"] = k("/edit")

# MongoDB config
app.config["MONGODB_DB"] = "ktest"
app.config["MONGODB_HOST"] = "localhost"
app.config["MONGODB_PORT"] = 27017

# only useful for keeping track of sessions in production; comment out when
# running on localhost, because SERVER_NAME needs to be a fully qualified
# domain name in order for sessions to work
# app.config["SERVER_NAME"] = "trnka.korpus.cz:5000"
# app.config["APPLICATION_ROOT"] = "/"

app.config["MAX_DISAMB_PASSES"] = 2

# these have to go last (circular imports)
import kudlanka.views
import kudlanka.api
