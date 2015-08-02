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
app.config["SECRET_KEY"] = "testing"
app.config["SECURITY_PASSWORD_HASH"] = "pbkdf2_sha512"
app.config["SECURITY_PASSWORD_SALT"] = "testing"
app.config["MONGODB_DB"] = "kudlanka"
app.config["MONGODB_HOST"] = "localhost"
app.config["MONGODB_PORT"] = 27017

# Utility functions


@app.context_processor
def utility_processor():
    """Define functions to make available to templates here and return them in a
    dictionary.

    """

    def wtf2bs(flash_class):
        """Translate flash class from WTF to Bootstrap."""
        if flash_class == "error":
            return "danger"
        else:
            return flash_class

    return dict(wtf2bs = wtf2bs)


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
    assigned = db.StringField(default = None)
    segs = db.ListField(db.StringField(), default = [])


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

    def to_mongo(self, *args, **kwargs):
        mongo = super(Seg, self).to_mongo(*args, **kwargs)
        mongo["_id"] = str(mongo["_id"])
        # for debugging mandisApp flash messages
        # mongo["messages"] = [{
        #     "type": "danger",
        #     "content": "Nastala chyba."
        # },
        # {
        #     "type": "danger",
        #     "content": "Nastala chyba."
        # }]
        return mongo


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


@app.before_first_request
def create_user():
    user_datastore.create_user(email="testing", password="testing")


# Routes

## UI


@app.route("/")
@login_required
def root():
    return redirect(url_for("list"))


@app.route("/list/")
@login_required
def list():
    return "Seznam promluv"


@app.route("/edit/")
@app.route("/edit/<string:sid>/")
@login_required
def edit(sid = None):
    return render_template("edit.html")


@app.route("/debug/")
def debug():
    if app.config["DEBUG"]:
        assert False
    else:
        pass


## API

api = Api(app, decorators = [login_required])


class SegSid(Resource):
    def get(self, sid):
        seg = Seg.objects(sid = sid).first()
        return seg.to_mongo()

    def post(self, sid):
        # the user can post a seg only if it's currently assigned to them
        pass


class SegAssign(Resource):
    def get(self, done):
        uid = session["user_id"]
        user = User.objects(id = uid).first()
        if user.assigned:
            seg = Seg.objects(sid = user.assigned).first()
            return seg.to_mongo()
        else:
            seg = Seg.objects(done = done,
                              assigned = False,
                              users__nin = uid).first()
            seg.modify(assigned = True, add_to_set__users = uid)
            user.modify(assigned = seg.sid, add_to_set__segs = seg.sid)
            return seg.to_mongo()


api.add_resource(SegSid, "/api/sid/<string:sid>/")
api.add_resource(SegAssign, "/api/assign/<int:done>/")
