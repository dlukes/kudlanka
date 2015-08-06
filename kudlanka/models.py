from flask.ext.mongoengine import MongoEngine
from flask.ext.security import MongoEngineUserDatastore, RoleMixin, UserMixin

from kudlanka import app

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


user_datastore = MongoEngineUserDatastore(db, User, Role)


# @app.before_first_request
# def create_user():
#     user_datastore.create_user(email="testing", password="testing")


## Data storage


class Seg(db.Document):         # DynamicDocument
    meta = {
        "collection": "segs",
        "indexes": [
            {"fields": ["sid"], "unique": True},
            {"fields": ["ambiguous", "users"]}
        ]
    }
    sid = db.StringField(max_length = 10, required = True)
    oral = db.StringField(max_length = 10, required = True)
    num = db.StringField(max_length = 10, required = True)
    ambiguous = db.StringField(required = True)
    # users to whom the seg has been assigned (irrespective of whether they
    # have comleted the assignment)
    users = db.ListField(required = True)
    utt = db.ListField(required = True)

    def to_mongo(self, *args, **kwargs):
        mongo = super(Seg, self).to_mongo(*args, **kwargs)
        mongo["_id"] = str(mongo["_id"])
        return mongo
