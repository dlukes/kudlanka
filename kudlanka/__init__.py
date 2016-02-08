from flask import Flask
from flask.json import JSONEncoder
from flask.ext.markdown import Markdown
from flask.ext.babel import lazy_gettext as _

from .config import k

import sys


class CustomJSONEncoder(JSONEncoder):
    """This class adds support for lazy translation texts to Flask's JSON encoder.
    This is necessary when flashing translated texts.

    See <http://blog.miguelgrinberg.com/post/using-flask-babel-with-flask-010>
    for details.

    """
    def default(self, obj):
        from speaklater import is_lazy_string
        if is_lazy_string(obj):
            try:
                return unicode(obj)  # python 2
            except NameError:
                return str(obj)  # python 3
        return super(CustomJSONEncoder, self).default(obj)


class Mail():
    def send(self, msg):
        pass


app = Flask(__name__, static_url_path=k("/static"))
app.json_encoder = CustomJSONEncoder
app.config.from_pyfile("config.py")
try:
    app.config.from_pyfile("../instance/secret_config.py")
except FileNotFoundError as e:
    print(e)
    print(_("Please provide a SECRET_KEY and a SECURITY_PASSWORD_SALT."))
    sys.exit(1)
Markdown(app)
# a dummy mail object to satisfy flask security, which keeps wanting to send
# e-mail to users about their actions
app.extensions["mail"] = Mail()

# these have to go last (circular imports) -- anything that's not imported by
# the modules listed hereunder also needs to be explicitly required here
import kudlanka.api
import kudlanka.babel
import kudlanka.forms
import kudlanka.views
