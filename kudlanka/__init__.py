from flask import *
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, RoleMixin, \
    UserMixin, login_required
from flask.ext.security.forms import LoginForm
from flask.ext.restful import Resource, Api

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

## User management


class Role(db.Document, RoleMixin):
    name = db.StringField(max_length = 80, unique = True)
    description = db.StringField(max_length=255)


class User(db.Document, UserMixin):
    email = db.StringField(max_length = 255)
    password = db.StringField(max_length = 255)
    active = db.BooleanField(default = True)
    roles = db.ListField(db.ReferenceField(Role), default = [])
    assigned = db.StringField()
    segs = db.ListField(db.StringField())


## Data storage


class Seg(db.Document):         # DynamicDocument
    meta = {
        "collection": "segs",
        "indexes": [
            {"fields": ["sid"], "unique": True},
            {"fields": ["done", "assigned", "users"]}
        ]
    }
    sid = db.StringField(max_length = 10, required = True)
    oral = db.StringField(max_length = 10, required = True)
    num = db.StringField(max_length = 10, required = True)
    done = db.IntField(required = True)
    assigned = db.BooleanField(required = True)
    users = db.ListField(required = True)
    utt = db.ListField(required = True)


segs = []
@app.before_first_request
def retrieve_unprocessed_segs():
    for seg in Seg.objects():
        segs.append(seg.sid)


# Flask-Security setup


class KudlankaLogin(LoginForm):
    email = TextField("Uživatel")
    password = PasswordField("Heslo")
    remember = BooleanField("Zapamatovat přihlášení")
    submit = SubmitField("Přihlásit se")


user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore, login_form = KudlankaLogin)

# Routes

## UI


@app.route("/")
@login_required
def root():
    return redirect(url_for("list"))


@app.route("/list")
@login_required
def list():
    return "Seznam promluv"


@app.route("/edit")
@login_required
def edit():
    return render_template("edit.html")


## API

api = Api(app, decorators = [login_required])


class SegApi(Resource):
    def get(self, sid):
        if sid == "random":
            seg = Seg.objects(done = 0,
                              assigned = False,
                              users__nin = session["user_id"]).first()
        else:
            seg = Seg.objects(sid = sid).first()
        seg = seg.to_mongo()
        seg["_id"] = str(seg["_id"])
        return seg


api.add_resource(SegApi, "/api/seg/<string:sid>")
