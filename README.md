# TODO

## Assigning already "done" segments

Remove done parameter from SegAssign API, make it a settable user property
instead...?

# Dev tips

- use `bower install` for fetching components like bootstrap, jquery, angular
  etc.
- use [Flask Assets](http://flask-assets.readthedocs.org/en/latest/) once it
  comes to minification
- keep track of python deps using `pip freeze >requirements.txt`
- REST validation with `reqparse` from `flask_restful`

## Production setup

- couldn't get setting `APPLICATION_ROOT` to work -- probably some problems in
  the config of the Apache2 proxy?
- defined a `k()` function instead, which is used to set a specified URL prefix
  wherever necessary in the app, i.e.:
  - server-side: for all routes
  - client-side: inside the `<base>` tag of html templates

→ turns out `APPLICATION_ROOT` is only relevant for setting cookies, it has
nothing to do with setting a prefix and ensuring correct redirection. Have a
look at [this snippet](http://flask.pocoo.org/snippets/35/) instead, or at
[blueprints](http://flask.pocoo.org/docs/0.10/blueprints/), which allow to
create instances of applications and wire them up at arbitrary prefixes (among
other things).

However, blueprints are not full-fledged apps, they can't have their own
sessions grafted onto them using Flask Security, for instance. For this reason,
it's not practical or straightforward to just package an app as a blueprint and
let it run under an arbitrary prefix in a container app.

Another possibility is to use `werkzeug.wsgi.DispatcherMiddleware`, again
creating a container app and wiring sub-apps on different URL prefixes. But
unfortunately, this isn't hassle-free either, various components tend to assume
they're running under root anyway unless explicitly told otherwise (Flask
Security routes, Flask Restful routes), introducing subtle breakage.

For this reason, explicitly wrapping every route in `k()` is probably the best
option -- extensions always have a way of altering individual routes, but they
might not have an option to set a universal URL prefix. NOTE: remember to also
`Flask(..., static_url_path = k("/static"))`!

## User registration

Bare views for registration provided by Flask Security are available by
uncommenting the appropriate config lines, but we don't actually want just
anyone to be able to register. Just fire up the `mongo kudlanka` shell and add
users manually with `db.user.insert({email: "username", password:
"password"})`. The password will be automatically hashed on first login.

# Name

Manuální disambiguace → mandis → mantis religiosa → kudlanka

# Requirements

See `bower.json` for client-side and `requirements.txt` for
server-side. Scripts under `utils/` may have additional dependencies, install
as needed.

# License

Copyright © 2015 David Lukeš

Distributed under the
[GNU General Public License v3](http://www.gnu.org/licenses/gpl-3.0.en.html).
