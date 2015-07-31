from flask import *
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, RoleMixin, \
    UserMixin, login_required
from flask.ext.security.forms import LoginForm

from wtforms import TextField, PasswordField, SubmitField, BooleanField

# App setup

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "super secret"
app.config["MONGODB_DB"] = "kudlanka"
app.config["MONGODB_HOST"] = "localhost"
app.config["MONGODB_PORT"] = 27017

# MongoDB setup

db = MongoEngine(app)


class Role(db.Document, RoleMixin):
    name = db.StringField(max_length = 80, unique = True)
    description = db.StringField(max_length=255)


class User(db.Document, UserMixin):
    email = db.StringField(max_length = 255)
    password = db.StringField(max_length = 255)
    active = db.BooleanField(default = True)
    roles = db.ListField(db.ReferenceField(Role), default = [])


# Flask-Security setup


class KudlankaLogin(LoginForm):
    email = TextField("Uživatel")
    password = PasswordField("Heslo")
    remember = BooleanField("Zapamatovat přihlášení")
    submit = SubmitField("Přihlásit se")


user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore, login_form = KudlankaLogin)

# Routes


@app.route("/")
@login_required
def root():
    return redirect(url_for("list"))


@app.route("/list")
@login_required
def list():
    return "Seznam promluv"


@app.route("/edit/<id>")
@login_required
def edit(id):
    return render_template("edit.html", id = id)
