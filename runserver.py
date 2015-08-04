from kudlanka import app
from flask import url_for

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

if app.config["SERVER_NAME"]:
    print("Listing available routes...")
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and has_no_empty_params(rule):
            with app.app_context():
                print(url_for(rule.endpoint))

app.run(debug = True, host = "localhost", port = 1993)

# the app is then accessible on the LAN via http://trnka:5000
