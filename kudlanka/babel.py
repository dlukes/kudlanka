from flask import request
from flask_babel import Babel
from flask_security import current_user

from kudlanka import app

babel = Babel(app)


@babel.localeselector
def get_locale():
    """i18n / l10n support -- match language reported by browser.

    """
    # if a user is logged in, honor their locale settings
    if current_user.is_authenticated:
        return current_user.locale
    langs = app.config["LANGUAGES"]
    return request.accept_languages.best_match(langs.keys())
