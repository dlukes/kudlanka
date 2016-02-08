from flask import Flask
from flask.json import JSONEncoder
from flask.ext.markdown import Markdown
from flask.ext.babel import lazy_gettext as _

from .config import k

import os
import sys
from git import Repo


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


def get_version():
    repo = Repo(search_parent_directories=True)
    tag = repo.tags[-1]
    head = repo.head.commit
    if tag.commit == head:
        return dict(type="tag", value=tag.name)
    return dict(type="commit", value=head.hexsha)


app = Flask(__name__, static_url_path=k("/static"))
app.json_encoder = CustomJSONEncoder
app.config.from_pyfile("config.py")
try:
    app.config.from_pyfile(os.path.join("..", "instance", "secret_config.py"))
except FileNotFoundError as e:
    print(e)
    print(_("Please provide a SECRET_KEY and a SECURITY_PASSWORD_SALT."))
    sys.exit(1)
app.config["VERSION"] = get_version()
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
