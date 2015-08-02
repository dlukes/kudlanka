from flask import *
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, RoleMixin, \
    UserMixin, login_required
from flask.ext.security.forms import LoginForm
from flask.ext.restful import Resource, Api, abort

from wtforms import TextField, PasswordField, SubmitField, BooleanField
from datetime import date

# App setup

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "testing"
app.config["SECURITY_PASSWORD_HASH"] = "pbkdf2_sha512"
app.config["SECURITY_PASSWORD_SALT"] = "testing"
app.config["MONGODB_DB"] = "kudlanka"
app.config["MONGODB_HOST"] = "localhost"
app.config["MONGODB_PORT"] = 27017

app.config["MAX_DISAMB_PASSES"] = 2

# Utility functions


@app.before_first_request
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

    def footer_date():
        start_year = 2015
        this_year = date.today().year
        if this_year > start_year:
            return str(start_year) + "&ndash;" + str(this_year)
        else:
            return str(start_year)

    return dict(wtf2bs = wtf2bs, footer_date = footer_date)


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
            {"fields": ["assigned", "ambiguous", "users"]}
        ]
    }
    sid = db.StringField(max_length = 10, required = True)
    oral = db.StringField(max_length = 10, required = True)
    num = db.StringField(max_length = 10, required = True)
    assigned = db.StringField(required = True)
    ambiguous = db.StringField(required = True)
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
    err = "Neoprávněný přístup."
    edit_err = "Nemáte právo editovat tento segment."
    len_err = ("Délka vkládaného segmentu neodpovídá délce segmentu pro SID {} v "
               "databázi.")
    word_err = ("Vkládané slovo {} neodpovídá slovu {} na {}. pozici v segmentu "
                "s SID {} v databázi.")
    miss_l_err = "Na {}. vkládané pozici prosím vyberte lemma."
    miss_t_err = "Na {}. vkládané pozici prosím vyberte tag."

    def get(self, sid):
        seg = Seg.objects(sid = sid).first()
        return seg.to_mongo()

    def post(self, sid):
        request.get_data()
        utt = request.json
        uid = session["user_id"]
        user = User.objects(id = uid).first()
        seg = Seg.objects(sid = sid).first()
        if uid not in seg.users + [seg.assigned]:
            abort(403,
                  messages = [["danger", SegSid.edit_err]])
        if not len(seg["utt"]) == len(utt):
            abort(400,
                  messages = [["danger", SegSid.len_err.format(sid)]])
        for i, dbpos, postpos in zip(range(1, len(seg["utt"]) + 1),
                                     seg["utt"],
                                     utt):
            if "lemma" not in postpos:
                abort(400, messages = [["warning",
                                        SegSid.miss_l_err.format(i)]])
            if "tag" not in postpos:
                abort(400, messages = [["warning",
                                        SegSid.miss_t_err.format(i)]])
            if dbpos["word"] == postpos["word"]:
                # only save flag if it's True (it might be present, but set to
                # False)
                if postpos.get("flag"):
                    dbpos.setdefault("flags", {})[uid] = True
                    # only save note if flag was True (a note might be present
                    # along with a False flag)
                    if "note" in postpos:
                        dbpos.setdefault("notes", {})[uid] = postpos["note"]
                else:
                    # the flag may also have been removed after having been
                    # added in an earlier POST; make sure it's gone by deleting
                    # it
                    dbpos.setdefault("flags", {}).pop(uid, None)
                    dbpos.setdefault("notes", {}).pop(uid, None)
                if "pool" not in dbpos:
                    continue
                elif postpos["lemma"] in dbpos["pool"]:
                    dbpos.setdefault("lemmas", {})[uid] = postpos["lemma"]
                else:
                    abort(400, messages = [["danger", SegSid.err]])
                if postpos["tag"] in dbpos["pool"].get(postpos["lemma"], {}):
                    dbpos.setdefault("tags", {})[uid] = postpos["tag"]
                else:
                    abort(400, messages = [["danger", SegSid.err]])
            else:
                abort(400,
                      messages = [["danger",
                                   SegSid.word_err.format(postpos["word"],
                                                          dbpos["word"], i,
                                                          sid)]])
        seg.modify(utt = seg["utt"], assigned = "", add_to_set__users = uid)
        user.modify(assigned = None)
        return {}, 201


class SegAssign(Resource):
    done_err = "Pro každý segment požadujeme max. {} hodnocení."
    noseg_err = ("V tuto chvíli pro vás není volný žádný segment s celkovým "
                 "počtem hodnocení {}.")

    def get(self, done):
        """Assign a segment which has already been disambiguated done times."""
        max_done = app.config["MAX_DISAMB_PASSES"]
        if done >= max_done:
            abort(403, messages = [["danger",
                                    SegAssign.done_err.format(max_done)]])
        uid = session["user_id"]
        user = User.objects(id = uid).first()
        if user.assigned:
            seg = Seg.objects(sid = user.assigned).first()
            return seg.to_mongo()
        else:
            seg = Seg.objects(assigned = "",
                              ambiguous = True,
                              users__size = done,
                              users__nin = [uid]).first()
            try:
                seg.modify(assigned = uid)
                user.modify(assigned = seg.sid, add_to_set__segs = seg.sid)
            except AttributeError:
                # seg is None
                abort(400,
                      messages = [["danger",
                                   SegAssign.noseg_err.format(done)]])
            return seg.to_mongo()


api.add_resource(SegSid, "/api/sid/<string:sid>/")
api.add_resource(SegAssign, "/api/assign/<int:done>/")
