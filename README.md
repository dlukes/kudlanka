# Dev tips

- use `bower install` for fetching components like bootstrap, jquery, angular
  etc.
- use [Flask Assets](http://flask-assets.readthedocs.org/en/latest/) once it
  comes to minification
- keep track of python deps using `pip freeze >requirements.txt`
- REST validation with `reqparse` from `flask_restful`

## Assigning already "done" segments

Remove done parameter from SegAssign API, make it a settable user property
instead...?

## Production setup

- couldn't get setting `APPLICATION_ROOT` to work -- probably some problems in
  the config of the Apache2 proxy?
- defined a `k()` function instead, which is used to set a specified URL prefix
  wherever necessary in the app, i.e.:
  - server-side: for all routes
  - client-side: inside the `<base>` tag of html templates

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
