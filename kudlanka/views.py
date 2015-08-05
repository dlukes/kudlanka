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

    return dict(wtf2bs = wtf2bs, footer_date = footer_date, k = k)


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
    for sid in reversed(user.segs):
        seg = Seg.objects(sid = sid).first()
        utt = " ".join(pos["word"] for pos in seg.utt)
        segs.append(dict(sid = seg.sid, oral = seg.oral, utt = utt))
    return render_template("list.html", segs = segs)


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
