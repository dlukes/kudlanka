# TODO

- rewrite app as wireable Blueprint
- refactor app into individual files, including sensitive config under
  `instance/` and "real" config files
- confirm navigation when form dirty
- display username in navbar

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
[blueprings](http://flask.pocoo.org/docs/0.10/blueprints/), which allow to
create instances of applications and wire them up at arbitrary prefixes (among
other things).

## User registration

Bare views for registration provided by Flask Security are available by
uncommenting the appropriate config lines, but we don't actually want just
anyone to be able to register. Just fire up the `mongo kudlanka` shell and add
users manually with `db.user.insert({email: "username", password:
"password"})`. The password will be automatically hashed on first login.

# Name

Manuální disambiguace → mandis → mantis religiosa → kudlanka

# Requirements

See for webapp, see `requirements.txt`. Scripts under `utils/` may have
additional dependencies, install as needed.
