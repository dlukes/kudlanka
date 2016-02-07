from flask import *
from flask.ext.security import Security, login_required, current_user, \
    url_for_security, roles_required
from flask.ext.security.forms import LoginForm, ChangePasswordForm, EqualTo, \
    Required, Length
from flask.ext.wtf import Form
from flask.ext.babel import Babel
from flask.ext.babel import lazy_gettext as _

from kudlanka import app
from .config import k, LANGUAGES
from .models import user_ds, User, Seg

from wtforms import TextField, PasswordField, SubmitField, BooleanField, \
    SelectField, IntegerField
from wtforms.validators import InputRequired, NumberRange, ValidationError
from datetime import date

# i18n / l10n
babel = Babel(app)


@babel.localeselector
def get_locale():
    """i18n / l10n support -- match language reported by browser.

    """
    # if a user is logged in, honor their locale settings
    if current_user.is_authenticated():
        return current_user.locale
    return request.accept_languages.best_match(LANGUAGES.keys())


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


# Forms and security routes


class AssignBatchForm(Form):
    batch_size = IntegerField(_("Batch size"), [
        InputRequired(message=_("Fill out the batch size field.")),
        NumberRange(min=1, message=_("Batch size must be > 0."))])
    user = SelectField(_("User"))
    submit = SubmitField(_("Assign"))

    def validate_user(self, field):
        user = User.objects(id=field.data).first()
        if len(user.segs) < sum(user.batches):
            raise ValidationError(_("The user already has a batch assigned."))


class SettingsForm(Form):
    locale = SelectField(_("Interface language"),
                         choices=app.config["LANGUAGES"].items())


email_required = Required(message='EMAIL_NOT_PROVIDED')
password_required = Required(message='PASSWORD_NOT_PROVIDED')
password_length = Length(min=6, max=128, message='PASSWORD_INVALID_LENGTH')


class AddUserForm(Form):
    email = TextField(_("User name (email)"), validators=[email_required])
    password = PasswordField(
        _("Password"),
        validators=[password_required, password_length])
    password_confirm = PasswordField(
        _("Retype password"),
        validators=[EqualTo("password", message="RETYPE_PASSWORD_MISMATCH")])
    submit = SubmitField(_("Add new user"))


class KudlankaLoginForm(LoginForm):
    email = TextField(_("User"))
    password = PasswordField(_("Password"))
    remember = BooleanField(_("Remember me"))
    submit = SubmitField(_("Log in"))


class KudlankaChangePasswordForm(ChangePasswordForm):
    password = PasswordField(_("Password"), validators=[password_required])
    new_password = PasswordField(
        _("New password"),
        validators=[password_required, password_length])
    new_password_confirm = PasswordField(
        _("Retype password"),
        validators=[EqualTo("new_password", message="RETYPE_PASSWORD_MISMATCH")])
    submit = SubmitField(_("Change password"))


security = Security(app, user_ds, login_form=KudlankaLoginForm,
                    change_password_form=KudlankaChangePasswordForm)

# Regular routes


@app.route(k("/"))
def root():
    if current_user.has_role("admin"):
        return redirect(url_for("admin"))
    if current_user.is_authenticated():
        return redirect(url_for("edit"))
    else:
        return redirect(url_for_security("login"))


@app.route(k("/list/"))
@login_required
def list():
    uid = session["user_id"]
    user = User.objects(id=uid).first()
    segs = []
    for i, sid in enumerate(user.segs):
        seg = Seg.objects(sid=sid).first()
        utt = []
        flag_seg = False
        for pos in seg.utt:
            utt.append(pos["word"])
            if pos.get("flags", {}).get(uid, False):
                flag_seg = True
        utt = " ".join(utt)
        segs.append(dict(i=i + 1, sid=seg.sid, oral=seg.oral, utt=utt,
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
        return redirect(url_for("admin"))
    elif au_form.submit.data and au_form.validate_on_submit():
        user_ds.create_user(email=au_form.email.data,
                            password=au_form.password.data)
        flash(_("New user successfully added."), "success")
        return redirect(url_for("admin"))
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
        return redirect(url_for("settings"))
    return render_template("settings.html", form=form)
