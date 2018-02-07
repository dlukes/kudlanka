from flask_security import Security
from flask_security.forms import LoginForm, ChangePasswordForm, EqualTo, \
    Required, Length
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as _

from kudlanka import app
from .models import User, user_ds

from wtforms import TextField, PasswordField, SubmitField, BooleanField, \
    SelectField, IntegerField
from wtforms.validators import InputRequired, NumberRange, ValidationError

email_required = Required(message='EMAIL_NOT_PROVIDED')
password_required = Required(message='PASSWORD_NOT_PROVIDED')
password_length = Length(min=6, max=128, message='PASSWORD_INVALID_LENGTH')

# Forms


class AssignBatchForm(FlaskForm):
    batch_size = IntegerField(_("Batch size"), [
        InputRequired(message=_("Fill out the batch size field.")),
        NumberRange(min=1, message=_("Batch size must be > 0."))])
    user = SelectField(_("User"))
    submit = SubmitField(_("Assign"))

    def validate_user(self, field):
        user = User.objects(id=field.data).first()
        if len(user.segs) < sum(user.batches):
            raise ValidationError(_("The user already has a batch assigned."))


class SettingsForm(FlaskForm):
    locale = SelectField(_("Interface language"),
                         choices=app.config["LANGUAGES"].items())


class AddUserForm(FlaskForm):
    email = TextField(_("User name (email)"), validators=[email_required])
    password = PasswordField(
        _("Password"),
        validators=[password_required, password_length])
    password_confirm = PasswordField(
        _("Retype password"),
        validators=[EqualTo("password", message="RETYPE_PASSWORD_MISMATCH")])
    submit = SubmitField(_("Add new user"))


# Security, including forms


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
