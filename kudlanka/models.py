from flask.ext.mongoengine import MongoEngine
from flask.ext.security import RoleMixin, UserMixin, MongoEngineUserDatastore

from kudlanka import app

db = MongoEngine(app)

# User management


class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)


class User(db.Document, UserMixin):
    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    roles = db.ListField(db.ReferenceField(Role), default=[])
    assigned = db.StringField(default=None)
    segs = db.ListField(db.StringField(), default=[])
    # a list of segment batches (each represented simply by the number of segs
    # to disambiguate) that the user has completed; the last one is the one
    # they are currently working on
    batches = db.ListField(db.IntField(), default=[])
    locale = db.StringField(max_length=5, default="en")


user_ds = MongoEngineUserDatastore(db, User, Role)


@app.before_first_request
def init():
    if not User.objects(email="admin"):
        admin = user_ds.create_user(
            email="admin",
            password=app.config.get("ADMIN_PASSWD", "admin"))
        a_role = user_ds.find_or_create_role(
            "admin",
            description="Admin role.")
        user_ds.add_role_to_user(admin, a_role)


# Data storage


class Seg(db.Document):         # or DynamicDocument
    meta = {
        "collection": "segs",
        "indexes": [
            {"fields": ["sid"], "unique": True},
            {"fields": ["ambiguous", "users", "users_size"]},
            {"fields": ["users_size"]}
        ]
    }
    sid = db.StringField(max_length=10, required=True)
    corpus = db.StringField(max_length=10, required=True)
    num = db.StringField(max_length=10, required=True)
    ambiguous = db.StringField(required=True)
    # users to whom the seg has been assigned (irrespective of whether they
    # have comleted the assignment)
    users = db.ListField(required=True)
    # we need to be able to order by len(users), but MongoDB doesn't support
    # this kind of query, so len(users) has to be kept track of separately
    users_size = db.IntField(required=True)
    utt = db.ListField(required=True)

    def to_mongo(self, *args, **kwargs):
        mongo = super(Seg, self).to_mongo(*args, **kwargs)
        mongo["_id"] = str(mongo["_id"])
        return mongo
