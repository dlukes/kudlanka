from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/<name>')
def hello(name = None):
    if name is None: name = "ICNC"
    return render_template("index.html", name = name)
