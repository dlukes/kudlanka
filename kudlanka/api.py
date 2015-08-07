from flask import *
from flask.ext.restful import Resource, Api, abort
from flask.ext.security import login_required

from kudlanka import app
from kudlanka.config import k
from kudlanka.models import Seg, User

from functools import wraps

api = Api(app, decorators = [login_required])


# decorate API calls with this to get user info
def user_info(api_call):

    @wraps(api_call)
    def wrapper(*args, **kwargs):
        uid = session["user_id"]
        user = User.objects(id = uid).first()
        user_info = dict(done = len(user.segs), max = user.batches[-1])
        response = api_call(*args, **kwargs)
        response.update(user = user_info)
        return response

    return wrapper


class SegSid(Resource):
    err = "Neoprávněný přístup."
    edit_err = "Nemáte právo editovat tento segment."
    len_err = ("Délka vkládaného segmentu neodpovídá délce segmentu pro SID {} v "
               "databázi.")
    word_err = ("Vkládané slovo {} neodpovídá slovu {} na {}. pozici v segmentu "
                "s SID {} v databázi.")
    miss_l_err = "Na {}. vkládané pozici prosím vyberte lemma."
    miss_t_err = "Na {}. vkládané pozici prosím vyberte tag."
    seg_err = "Segment s SID {} neexistuje."
    method_decorators = [user_info]

    def get(self, sid):
        seg = Seg.objects(sid = sid).first()
        if seg is None:
            abort(400,
                  messages = [["danger", SegSid.seg_err.format(sid)]])
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
        user = User.objects(id = uid).first()
        seg = Seg.objects(sid = sid).first()
        if uid not in seg.users:
            abort(403,
                  messages = [["danger", SegSid.edit_err]])
        if not len(seg["utt"]) == len(utt):
            abort(400,
                  messages = [["danger", SegSid.len_err.format(sid)]])
        for i, dbpos, postpos in zip(range(1, len(seg["utt"]) + 1),
                                     seg["utt"],
                                     utt):
            if not postpos.get("lemma", False):
                abort(400, messages = [["warning",
                                        SegSid.miss_l_err.format(i)]])
            if not postpos.get("tag", False):
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
        seg.modify(utt = seg["utt"])
        # only remove segment assignment if the user is currently posting their
        # most recently asssigned segment, which means they're ready to be
        # assigned a new one (otherwise they're just re-editing a segment from
        # their history, in which case we want them to keep the segment they
        # have been assigned)
        if user.assigned == seg.sid:
            user.modify(assigned = None)
        return {}


class SegAssign(Resource):
    done_err = "Pro každý segment požadujeme max. {} hodnocení."
    noseg_err = ("V tuto chvíli pro vás není volný žádný segment s celkovým "
                 "počtem hodnocení {}.")
    method_decorators = [user_info]

    def get(self, done):
        """Assign a segment which has already been disambiguated done times."""
        max_done = app.config["MAX_DISAMB_PASSES"]
        if done >= max_done:
            abort(403, messages = [["danger",
                                    SegAssign.done_err.format(max_done)]])
        uid = session["user_id"]
        user = User.objects(id = uid).first()
        if user.assigned:
            seg = Seg.objects(sid = user.assigned).first().to_mongo()
            return seg
        else:
            seg = Seg.objects(ambiguous = True,
                              users__size = done,
                              users__nin = [uid]).first()
            try:
                seg.modify(add_to_set__users = uid)
                user.modify(assigned = seg.sid, add_to_set__segs = seg.sid)
            except AttributeError:
                # seg is None
                abort(400,
                      messages = [["danger",
                                   SegAssign.noseg_err.format(done)]])
            return seg.to_mongo()


api.add_resource(SegSid, k("/api/sid/<string:sid>/"))
api.add_resource(SegAssign, k("/api/assign/<int:done>/"))
