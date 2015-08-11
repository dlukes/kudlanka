from flask import Flask

from kudlanka.config import k

import sys

app = Flask(__name__, static_url_path=k("/static"))
app.config.from_pyfile("config.py")
try:
    app.config.from_pyfile("../instance/secret_config.py")
except FileNotFoundError as e:
    print(e)
    print("Please provide a SECRET_KEY and a SECURITY_PASSWORD_SALT.")
    sys.exit(1)

# these have to go last (circular imports)
import kudlanka.views
import kudlanka.api
