from flask import Flask, render_template, redirect, url_for, request, flash
from database import db_session
from models import User, Order
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from random import randint
from collections import Counter

app = Flask(__name__)
app.secret_key = b'supersecretcode'

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"
login_manager.login_message = "Please sign in to access this page"
login_manager.login_message_category = "info"


@app.route("/")
def home_page():
    if current_user.is_authenticated:
        return redirect(url_for('account_page'))
    return redirect(url_for("login_page"))


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
        u.time = "12:00 14:00"
        db_session.add(u)
        db_session.commit()
        flash("Welcome to our site !","success")
        login_user(u)
        return redirect(url_for("home_page"))


@login_required
@app.route("/account/")
def account_page():
    u = load_user(current_user.get_id())
    parti = u.participants.split()  # participants
    res = u.restaurants.split() # restaurants
    time = u.time.split()
    all_parti = parti[:]
    all_parti.append(u.name)
    ord = Order.query.filter(Order.name.in_(all_parti)).all()  # past orders
    # making an order
    if ord and parti:
        # wiot configurations
        last_ord = ord[-1]

        parti.insert(0,u.name)
        last_person = last_ord.name
        if last_person in parti:
            index = parti.index(last_person)
            total_index = len(parti)-1
            if index == total_index:
                wiot = parti[0]
            else:
                wiot = parti[index+1]
        else:
            wiot = parti[0]

        # restaurant config
        last_rest = last_ord.restaurant
        if last_rest in res:
            index_res = res.index(last_rest)
            total_index_res = len(res)-1
            if index_res == total_index_res:
                next_rest = res[0]
            else:
                next_rest = res[index_res+1]
        else:
            if res:
                next_rest = res[0]
            else:
                next_rest = ""
        parti.pop(0)
    else:
        wiot = u.name   # wiot = Who Is Ordering Today
        next_rest = res[0] if res else ""


    fav_meal = {}
    if ord:
        # finding favorite meal
        for para in all_parti:
            meals = []
            for o1 in ord:
                dict1 = dict(e.split(' : ') for e in o1.orders.split(','))
                meals.append(dict1.get(para))
            cnt = Counter(meals).most_common()[0][0]
            fav_meal[para] = cnt

        # finding favorite time and restaurant
        times = []
        restaurants = []
        for order in ord:
            list1 = list(order.time)
            del list1[2]
            time2 = int("".join(list1))
            times.append(time2)
            restaurants.append(order.restaurant)
        avg_times = int(sum(times)/len(times))
        avg_time2 = list(str(avg_times))
        avg_time2.insert(2,":")
        avg_time3 = "".join(avg_time2)
        fav_restaurants = Counter(restaurants).most_common()[0][0]
    else:
        avg_time3 = "No Data"
        fav_restaurants = "No Data"
    non_order = False if ord else True
    time_order = random_hour(time[0],time[1])   # generate random hour to eat
    non_rest = False if res else True
    return render_template("account_page.html",non_order=non_order,fav_meal=fav_meal,non_rest=non_rest,
                           time_order=time_order, next_rest=next_rest, user=u,parti=parti,wiot=wiot,
                           ord=ord, res=res,time=time, fav_restaurants=fav_restaurants,avg_times=avg_time3)


# function for generate random hour
def random_hour(start,end):
    list1 = list(start)
    del list1[2]
    list2 = list(end)
    del list2[2]
    start = int("".join(list1))
    end = int("".join(list2))
    num = end-start
    num2 = str(start+randint(0,num))
    if int(num2[-2]) > 5:
        num3 = list(num2)
        num3[-2] = str(randint(int(list1[2]),int(list2[2])))
        str1 = "".join(num3)
        num2 = str1

    list3 = list(str(num2))
    list3.insert(2,":")
    return "".join(list3)


@login_required
@app.route("/account/make_the_order/",methods=["POST"])
def make_the_order():
    u = load_user(current_user.get_id())
    orders = ""
    for parti in u.participants.split():
        orders += parti + " : " +request.form[f"{parti}_meal"]+", "

    orders += u.name + " : " + request.form[u.name+"_meal"]

    order = Order(request.form["wiot"])
    order.restaurant = request.form["rest"]
    order.time = request.form["time_of_order"]
    order.orders = orders
    db_session.add(order)
    db_session.commit()
    flash("You've just made the order !","success")
    return redirect(url_for("account_page"))


# time configuration
@login_required
@app.route("/account/change_time/",methods=["POST"])
def change_time():
    new_time = request.form["time_from"] + " " + request.form["time_to"]
    u = load_user(current_user.get_id())
    u.time = new_time
    db_session.commit()
    return redirect(url_for("account_page"))


# participants configuration
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


# restaurants configuration
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


# load user from db
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == user_id).first()


# closing connection with db
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == "__main__":
    app.run(debug=True)