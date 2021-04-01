from flask import Flask, render_template, redirect, url_for, request, flash, session
from database import db_session
from models import User, Order
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


@app.route("/sign_out/")
@login_required
def logout():
    logout_user()
    flash("We looking forward to see you again !","success")
    return redirect(url_for("home_page"))


@app.route('/sign_up/')
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    return render_template("register_page.html")


@app.route('/sign_up/',methods=["POST"])
def register_page2():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    user1 = User.query.filter(User.email == email).first()
    user2 = User.query.filter(User.name == username).first()

    if user1:
        flash("User with this email address already exist.","danger")
        return render_template("register_page.html",username=username)
    elif user2:
        flash("User with this username already exist.","danger")
        return render_template("register_page.html", email=email)
    else:
        u = User(username,email)
        u.set_password(password)
        db_session.add(u)
        db_session.commit()
        flash("Welcome to our site !","success")
        login_user(u)
        return redirect(url_for("home_page"))


@login_required
@app.route("/account/")
def account_page():
    u = load_user(current_user.get_id())

    # participants
    parti = u.participants.split()
    res = u.restaurants.split()
    ord = Order.query.filter(User.name in parti).first()
    return render_template("account_page.html", user=u, parti=parti, ord=ord, res=res)


@login_required
@app.route("/account/add_participant/",methods=["POST"])
def add_parti():
    u = load_user(current_user.get_id())
    u.participants += request.form["name"] + " "
    db_session.commit()
    return redirect(url_for("account_page"))


@login_required
@app.route("/account/delete_participant/<name>/")
def delete_parti(name):
    u = load_user(current_user.get_id())
    parti = u.participants.split()
    parti.remove(name)
    names = ' '.join([str(elem) for elem in parti])
    u.participants = names
    db_session.commit()
    return redirect(url_for("account_page"))


@login_required
@app.route("/account/add_restaurant/",methods=["POST"])
def add_rest():
    u = load_user(current_user.get_id())
    u.restaurants += request.form["name-res"] + " "
    db_session.commit()
    return redirect(url_for("account_page"))


@login_required
@app.route("/account/delete_restaurants/<name>/")
def delete_rest(name):
    u = load_user(current_user.get_id())
    rest = u.restaurants.split()
    rest.remove(name)
    names = ' '.join([str(elem) for elem in rest])
    u.restaurants = names
    db_session.commit()
    return redirect(url_for("account_page"))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == user_id).first()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == "__main__":
    app.run(debug=True)