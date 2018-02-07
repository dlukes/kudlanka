from flask import abort, flash, g, redirect, render_template, request, \
    session, url_for
from flask_security import login_required, current_user, \
    url_for_security, roles_required
from flask_babel import lazy_gettext as _

from kudlanka import app
from .babel import get_locale
from .config import k
from .forms import AddUserForm, AssignBatchForm, SettingsForm
from .models import user_ds, User, Seg

import os
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

    utils = locals()
    utils.update(k=k)

    return utils


@app.before_request
def before_request():
    g.locale = get_locale()
    g.version = app.config["VERSION"]
    g.github = app.config["GITHUB"]


# Routes


@app.route(k("/"))
def root():
    if current_user.has_role("admin"):
        return redirect(url_for("admin"), 303)
    if current_user.is_authenticated:
        return redirect(url_for("edit"), 303)
    else:
        return redirect(url_for_security("login"), 303)


@app.route(k("/list/"))
@login_required
def list():
    # admin users don't have their own segments, so they don't have a list view
    if current_user.has_role("admin"):
        return redirect(url_for("admin"), 303)
    uid = session["user_id"]
    user = User.objects(id=uid).first()
    segs = []
    # FIXME: refactor this to preferably hit the db only once in order to
    # retrieve a user's segments (hitting it repeatedly for each segment is
    # a huge performance killer)
    for i, sid in enumerate(user.segs):
        seg = Seg.objects(sid=sid).first()
        utt = []
        flag_seg = False
        for pos in seg.utt:
            utt.append(pos["word"])
            if pos.get("flags", {}).get(uid, False):
                flag_seg = True
        utt = " ".join(utt)
        segs.append(dict(i=i + 1, sid=seg.sid, corpus=seg.corpus, utt=utt,
                         flag_seg=flag_seg))
    total = 0
    batches = []
    for batch, batch_size in enumerate(user.batches):
        # all batches except the last one are by definition done
        batches.append(dict(batch=batch + 1, assigned=batch_size,
                            done=batch_size, remaining=0))
        total += batch_size
    # correct stats for the last batch
    penalty = 1 if user.assigned else 0
    remaining = total - len(segs) + penalty
    done = user.batches[-1] - remaining
    batches[-1].update(done=done, remaining=remaining)
    return render_template("list.html", segs=segs, batches=batches)


@app.route(k("/edit/"))
@app.route(k("/edit/<string:sid>/"))
# the sid is handled client-side by angular
@login_required
def edit(sid=None):
    return render_template("edit.html")


@app.route(k("/debug/"))
def debug():
    if app.config["DEBUG"]:
        assert False
    else:
        abort(403, "Debug mode disabled.")


@app.route(k("/admin/"), methods=["GET", "POST"])
@roles_required("admin")
def admin():
    users = []
    for user in User.objects():
        if user.batches:
            penalty = 1 if user.assigned else 0
            done = len(user.segs) - penalty
            users.append(dict(assigned=sum(user.batches),
                              done=done, id=user.email))
    ab_form = AssignBatchForm(prefix="ab")
    ab_form.user.choices = [(str(u.id), u.email) for u
                            in User.objects(email__nin=["admin"])]
    au_form = AddUserForm(prefix="au")
    if ab_form.submit.data and ab_form.validate_on_submit():
        User.objects(
            id=ab_form.user.data).first().modify(
            push__batches=ab_form.batch_size.data)
        flash(_("New batch successfully added."), "success")
        return redirect(url_for("admin"), 303)
    elif au_form.submit.data and au_form.validate_on_submit():
        user_ds.create_user(email=au_form.email.data,
                            password=au_form.password.data)
        flash(_("New user successfully added."), "success")
        return redirect(url_for("admin"), 303)
    return render_template("admin.html", users=users, ab_form=ab_form,
                           au_form=au_form)


@app.route(k("/settings"), methods=["GET", "POST"])
def settings():
    form = SettingsForm(request.form, locale=current_user.locale)
    if form.validate_on_submit():
        current_user.update(set__locale=form.locale.data)
        flash(_("Settings updated."), "success")
        # redirect is necessary for new locale settings to apply -- start a new
        # request, re-fetch locale settings
        return redirect(url_for("settings"), 303)
    return render_template("settings.html", form=form)


@app.route(k("/docs/<string:locale>/<string:page>"))
def docs(locale, page):
    path = os.path.join("static", "docs", locale, page)
    if not os.path.isfile(path):
        path = os.path.join("static", "docs", "default", page)
    try:
        with app.open_resource(path) as fh:
            md = fh.read().decode("utf-8")
        return render_template("docs.html", md=md)
    except FileNotFoundError:
        abort(404, _("Requested document does not exist."))
