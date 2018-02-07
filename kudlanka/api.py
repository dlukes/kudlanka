from flask import *
from flask_restful import Resource, Api
import flask_restful as rest
from flask_security import login_required
from flask_babel import lazy_gettext as _

from kudlanka import app
from kudlanka.config import k
from kudlanka.models import Seg, User

from functools import wraps

api = Api(app, decorators=[login_required])


def get_user_info():
    uid = session["user_id"]
    user = User.objects(id=uid).first()
    # there's a difference between a user with len(user.segs) == X and no seg
    # assigned (that one's done) and a user with len(user.segs) == X and a
    # pending assignment (that one's still got one seg to go)
    penalty = 1 if user.assigned else 0
    done = len(user.segs) - sum(user.batches[:-1]) - penalty
    return dict(done=done, max=user.batches[-1])


# decorate API calls with this to get user info
def with_user_info(api_call):

    @wraps(api_call)
    def wrapper(*args, **kwargs):
        # api_call might modify user.segs → call it first
        response = api_call(*args, **kwargs)
        response.update(user=get_user_info())
        return response

    return wrapper


def abort(status_code, **kwargs):
    kwargs.update(user=get_user_info())
    return rest.abort(status_code, **kwargs)


class SegSid(Resource):
    edit_err = _("You are not allowed to edit this segment.")
    len_err = _(
        "The length of the segment being inserted does not match the length "
        "of segment with SID {0} in the database.")
    word_err = _(
        "The word being inserted ({0}) does not match the word ({1}) at "
        "position {2} in segment with SID {3} in the database.")
    miss_l_err = _("Pick lemma at position {0}.")
    miss_t_err = _("Pick tag at position {0}.")
    seg_err = _("Segment with SID {0} does not exist.")
    method_decorators = [with_user_info]

    def get(self, sid):
        seg = Seg.objects(sid=sid).first()
        if seg is None:
            abort(400, messages=[["danger", SegSid.seg_err.format(sid)]])
        seg = seg.to_mongo()
        uid = session["user_id"]
        for pos in seg["utt"]:
            if pos.get("lemmas", None):
                pos["lemma"] = pos["lemmas"].get(uid, None)
            if pos.get("tags", None):
                pos["tag"] = pos["tags"].get(uid, None)
            pos["flag"] = pos.get("flags", {}).get(uid, None)
            pos["note"] = pos.get("notes", {}).get(uid, None)
        return seg

    def post(self, sid):
        request.get_data()
        utt = request.json
        uid = session["user_id"]
        user = User.objects(id=uid).first()
        seg = Seg.objects(sid=sid).first()
        if uid not in seg.users:
            abort(403, messages=[["danger", SegSid.edit_err.format()]])
        if not len(seg["utt"]) == len(utt):
            abort(400, messages=[["danger", SegSid.len_err.format(sid)]])
        # iterate over positions in both db and post data, perform checks,
        # modify positions in db representation, then commit it
        for i, dbpos, postpos in zip(range(1, len(seg["utt"]) + 1),
                                     seg["utt"],
                                     utt):
            if not postpos.get("lemma", False):
                abort(400, messages=[["warning", SegSid.miss_l_err.format(i)]])
            if not postpos.get("tag", False):
                abort(400, messages=[["warning", SegSid.miss_t_err.format(i)]])
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
                for lemma in postpos["lemmas"]:
                    custom = lemma not in dbpos["pool"]
                    lemma = dict(value=lemma, custom=custom)
                    uid2lemmas = dbpos.setdefault("lemmas", {})
                    lemmas = uid2lemmas.setdefault(uid, [])
                    lemmas.append(lemma)
                for tag in postpos["tags"]:
                    custom = tag not in dbpos["pool"].get(postpos["lemma"], {})
                    tag = dict(value=tag, custom=custom)
                    uid2tags = dbpos.setdefault("tags", {})
                    tags = uid2tags.setdefault(uid, [])
                    tags.append(tag)
            else:
                error = SegSid.word_err.format(postpos["word"], dbpos["word"], i, sid)
                abort(400, messages=[["danger", error]])
        seg.modify(utt=seg["utt"])
        # only remove segment assignment if the user is currently posting their
        # most recently asssigned segment, which means they're ready to be
        # assigned a new one (otherwise they're just re-editing a segment from
        # their history, in which case we want them to keep the segment they
        # have been assigned)
        if user.assigned == seg.sid:
            user.modify(assigned=None)
        return {}


class SegAssign(Resource):
    noseg_err = _("Currently unable to assign new segment.")
    done = _("You're done :) Ask the admin for a new batch.")
    method_decorators = [with_user_info]

    def get(self):
        max_done = app.config["MAX_DISAMB_PASSES"]
        uid = session["user_id"]
        user = User.objects(id=uid).first()
        if user.assigned:
            seg = Seg.objects(sid=user.assigned).first().to_mongo()
            return seg
        # if user.assigned == "", then the user has completed all segs in
        # user.segs and might be done with their batch
        elif len(user.segs) >= sum(user.batches):
            abort(404, messages=[["success", SegAssign.done.format()]])
        else:
            # assign the already rated (i.e. the most rated → order_by) segs
            # first
            seg = Seg.objects(ambiguous=True,
                              users_size__lt=max_done,
                              users__nin=[uid]).order_by("-users_size").first()
            try:
                users = set(seg.users + [uid])
                users_size = len(users)
                seg.modify(users=users, users_size=users_size)
                user.modify(assigned=seg.sid, add_to_set__segs=seg.sid)
            except AttributeError:
                # seg is None
                abort(400, messages=[["danger", SegAssign.noseg_err.format()]])
            return seg.to_mongo()


api.add_resource(SegSid, k("/api/sid/<string:sid>/"))
api.add_resource(SegAssign, k("/api/assign/"))
