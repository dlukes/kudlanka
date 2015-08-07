from flask import *
from flask.ext.security import Security, login_required, current_user, \
    url_for_security
from flask.ext.security.forms import LoginForm

from kudlanka import app
from kudlanka.config import k
from kudlanka.models import user_datastore, User, Seg

from wtforms import TextField, PasswordField, SubmitField, BooleanField
from datetime import date

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

    def progress_color(batch):
        common = "progress-bar-"
        progress = batch["done"] / batch["assigned"]
        if progress < .25:
            return common + "danger"
        elif progress < .5:
            return common + "warning"
        elif progress < .75:
            return common + "info"
        else:
            return common + "success"

    return dict(wtf2bs = wtf2bs, footer_date = footer_date, k = k,
                progress_color = progress_color)


# Security routes


class KudlankaLogin(LoginForm):
    email = TextField("Uživatel")
    password = PasswordField("Heslo")
    remember = BooleanField("Zapamatovat přihlášení")
    submit = SubmitField("Přihlásit se")


security = Security(app, user_datastore, login_form = KudlankaLogin)

# Regular routes


@app.route(k("/"))
def root():
    if current_user.is_authenticated():
        return redirect(url_for("edit"))
    else:
        return redirect(url_for_security("login"))


@app.route(k("/list/"))
@login_required
def list():
    uid = session["user_id"]
    user = User.objects(id = uid).first()
    segs = []
    for i, sid in enumerate(user.segs):
        seg = Seg.objects(sid = sid).first()
        utt = []
        flag_seg = False
        for pos in seg.utt:
            utt.append(pos["word"])
            if pos.get("flags", {}).get(uid, False):
                flag_seg = True
        utt = " ".join(utt)
        segs.append(dict(i = i + 1, sid = seg.sid, oral = seg.oral, utt = utt,
                         flag_seg = flag_seg))
    total = 0
    batches = []
    for batch, batch_size in enumerate(user.batches):
        # all batches except the last one are by definition done
        batches.append(dict(batch = batch + 1, assigned = batch_size,
                            done = batch_size, remaining = 0))
        total += batch_size
    # correct stats for the last batch
    penalty = 1 if user.assigned else 0
    remaining = total - len(segs) + penalty
    done = user.batches[-1] - remaining
    batches[-1].update(done = done, remaining = remaining)
    return render_template("list.html", segs = segs, batches = batches)


@app.route(k("/edit/"))
@app.route(k("/edit/<string:sid>/"))
# the sid is handled client-side by angular
@login_required
def edit(sid = None):
    return render_template("edit.html")


@app.route(k("/debug/"))
def debug():
    if app.config["DEBUG"]:
        assert False
    else:
        pass
