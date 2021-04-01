from flask import Flask, render_template
from database import db_session
from models import User

app = Flask(__name__)


@app.route("/")
def home_page():
    return render_template("index.html")


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == "__main__":
    app.run(debug=True)