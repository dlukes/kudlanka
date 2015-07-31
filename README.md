# Dev tips

- use `bower install` for fetching components like bootstrap, jquery, angular etc.
- use [Flask Assets](http://flask-assets.readthedocs.org/en/latest/) once it
  comes to minification
- keep track of python deps using `pip freeze >requirements.txt`
- REST validation with `reqparse` from `flask_restful`

- for each seg, keep track of whether it has been::
    - done once
    - done twice
    - currently assigned
- once a seg is assigned, a given editor must complete it and no other editor
  must be able to access it

# Name

Manuální disambiguace → mandis → mantis religiosa → kudlanka

# Requirements

See for webapp, see `requirements.txt`. Scripts under `utils/` may have
additional dependencies, install as needed.
