from flask import Flask, render_template, redirect, url_for, request, flash
from database import db_session
from models import User
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = b'\xab\xfa&\xb9\x9eB\xd4\x07[\x00\xea~\xb1\xd7tj'

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"
login_manager.login_message = "Please sign in to access this page"
login_manager.login_message_category = "info"


@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/sign_in/",methods=["GET"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    return render_template("login_page.html")


@app.route('/sign_in/', methods=['POST'])
def login_page2():
    email = request.form["email"]
    password = request.form["password"]

    user_1 = User.query.filter(User.email == email).first()
    if user_1 and user_1.check_password(password):
        try:
            remember_me = True if request.form["remember_me"] == "on" else False
        except:
            remember_me = False
        login_user(user_1,remember=remember_me)
        flash(f"Welcome {user_1.name} !","success")
    else:
        flash("Incorrect email or password","danger")
        return redirect(url_for(".login_page"))

    return redirect(url_for('home_page'))


@app.route("/sign_out")
@login_required
def logout():
    logout_user()
    flash("We looking forward to see you again !","success")
    return redirect(url_for("home_page"))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == user_id).first()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == "__main__":
    app.run(debug=True)