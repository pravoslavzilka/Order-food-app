from flask import Flask, render_template, redirect, url_for, request, flash
from database import db_session
from models import User, Order
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from random import randint
from collections import Counter

app = Flask(__name__)
app.secret_key = b'supersecretcode'     # code for the session cookies

# flask-login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"     # page to redirect for login
login_manager.login_message = "Please sign in to access this page"  # flash message for non-login users
login_manager.login_message_category = "info"


@app.route("/")
def home_page():
    if current_user.is_authenticated:
        return redirect(url_for('account_page'))
    return redirect(url_for("login_page"))


@app.route("/sign_in/",methods=["GET"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))   # if the current user is logged in yet redirect to account
    return render_template("login_page.html")


@app.route('/sign_in/', methods=['POST'])
def login_page2():
    email = request.form["email"]               # take data from the forms
    password = request.form["password"]

    user_1 = User.query.filter(User.email == email).first()  # grab the user with this email
    if user_1 and user_1.check_password(password):           # if the password is correct
        try:
            remember_me = True if request.form["remember_me"] == "on" else False    # check remember me check box
        except:
            remember_me = False
        login_user(user_1,remember=remember_me)             # login the user
        flash(f"Welcome {user_1.name} !","success")         # flash message
    else:
        flash("Incorrect email or password","danger")       # if the email or password is incorrect
        return redirect(url_for(".login_page"))             # back to login_page

    return redirect(url_for('home_page'))


@app.route("/sign_out/")
@login_required
def logout():
    logout_user()             # function from login manager to logout user
    flash("We looking forward to see you again !","success")
    return redirect(url_for("home_page"))


@app.route('/sign_up/')
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))   # same as login page
    return render_template("register_page.html")


@app.route('/sign_up/',methods=["POST"])        # function accept only post methods
def register_page2():
    username = request.form["username"]
    email = request.form["email"]               # take the data from the forms
    password = request.form["password"]
    user1 = User.query.filter(User.email == email).first()      # check if the user with this email already exist
    user2 = User.query.filter(User.name == username).first()    # check if the user with this name already exist

    if user1:
        flash("User with this email address already exist.","danger")   # back to register page
        return render_template("register_page.html",username=username)
    elif user2:
        flash("User with this username already exist.","danger")
        return render_template("register_page.html", email=email)       # back to register page
    else:
        u = User(username,email)        # make the User object
        u.set_password(password)        # hash the password
        u.time = "12:00 14:00"          # set default time
        db_session.add(u)               # add the new to database
        db_session.commit()             # commit changes in database
        flash("Welcome to our site !","success")
        login_user(u)                   # login the user
        return redirect(url_for("home_page"))   # back to the home page


@login_required
@app.route("/account/")
def account_page():
    u = load_user(current_user.get_id())
    parti = u.participants.split()                          # user's participants
    res = u.restaurants.split()                             # user's restaurants
    time = u.time.split()                                   # user's time
    all_parti = parti[:]                                    # copy list with participants
    all_parti.append(u.name)                                # add admin to the new list
    ord = Order.query.filter(Order.name.in_(all_parti)).all()  # past orders
    # making an order
    if ord and parti:
        # wiot configurations wiot = Who Is Ordering Today
        last_ord = ord[-1]                                  # load last user's order
        parti.insert(0,u.name)                              # add admin to list of participants
        last_person = last_ord.name                         # find person who last ordered
        if last_person in parti:                            # if the person is still in participants
            index = parti.index(last_person)                # get index of the person in the list
            total_index = len(parti)-1                      # finding the total index
            if index == total_index:                        # if the last person was last in the list
                wiot = parti[0]                             # then the next person wil be the first in the list
            else:
                wiot = parti[index+1]                       # else the next person will be the next person in the list
        else:
            wiot = parti[0]                                 # if the last person isn't in the list, the next person will be the first in the list

        # restaurant config
        last_rest = last_ord.restaurant                     # same process as with user, but now also check if there is some restaurant
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
            else:                                           # if there isn't make the restaurant none
                next_rest = ""
        parti.pop(0)                                        # delete admin from the list to make it better to use in the template
    else:
        wiot = u.name                                       # wiot = Who Is Ordering Today
        next_rest = res[0] if res else ""                   # check if there is restaurant
    fav_meal = {}
    if ord:
        # finding favorite meal --- i will comment it when it will work properly
        for para in all_parti:
            meals = []
            for o1 in ord:
                dict1 = dict(e.split(' : ') for e in o1.orders.split(','))
                meals.append(dict1.get(para))
            cnt = Counter(meals).most_common()[0][0]
            fav_meal[para] = cnt

        # finding favorite restaurant
        times = []
        restaurants = []
        for order in ord:                           # list the orders
            list1 = list(order.time)                # converting the time string to list to be able to modify it
            del list1[2]                            # deleting ":" from the time string to able converting to integer
            time2 = int("".join(list1))             # converting time to integer tbe able to make an average
            times.append(time2)                     # add time to list of other times to make an average
            restaurants.append(order.restaurant)    # also want to find favorite restaurant so res. from oder is add to list of res. of other orders to find the favorite one
        avg_times = int(sum(times)/len(times))      # make the average of the times
        avg_time2 = list(str(avg_times))            # making it list to be able to insert ":" and check the time
        if int(avg_time2[2]) > 5:                   # if minutes are > 60 crop it, and add to hours 1
            avg_time2[2] = str(int(avg_time2[2])-6)
            avg_time2[1] = str(int(avg_time2[1])+1)
        avg_time2.insert(2,":")                     # make the string time string
        avg_time3 = "".join(avg_time2)              # make the list string
        fav_restaurants = Counter(restaurants).most_common()[0][0]  # find the favorite restaurant with Counter from list of restaurants
    else:
        avg_time3 = "No Data"                       # if there aren't any orders display "No data"
        fav_restaurants = "No Data"
    non_order = False if ord else True              # make the variable if are the orders to use it in html page
    time_order = random_hour(time[0],time[1])       # generate random hour to eat
    non_rest = False if res else True               # check if the user has any restaurant to unable the orders if he doesn't have
    return render_template("account_page.html",non_order=non_order,fav_meal=fav_meal,non_rest=non_rest,
                           time_order=time_order, next_rest=next_rest, user=u,parti=parti,wiot=wiot,
                           ord=ord, res=res,time=time, fav_restaurants=fav_restaurants,avg_times=avg_time3) # render html


# function for generate random hour
def random_hour(start,end):
    list1 = list(start)                             # making the string list to be able to modify it
    del list1[2]                                    # deleting ":" from the string to be able to convert it to integer
    list2 = list(end)                               # same for second hour
    del list2[2]
    start = int("".join(list1))                     # make it integer to be able to operate with randint
    end = int("".join(list2))
    num = end-start                                 # make the range
    num2 = str(start+randint(0,num))                # making the actual random hour
    if int(num2[-2]) > 5:                           # if the minutes are > 60 replace it with random digit from 0 to 6
        num3 = list(num2)
        num3[-2] = str(randint(int(list1[2]),int(list2[2])))
        str1 = "".join(num3)                       # make the list string
        num2 = str1

    list3 = list(str(num2))                        # again converting it to list to be able to insert ":"
    list3.insert(2,":")                            # i know its duplicate process but i want to unite the function at the end
    return "".join(list3)                          # return the actual random time in string time format


# write the order to database
@login_required
@app.route("/account/make_the_order/",methods=["POST"])
def make_the_order():
    u = load_user(current_user.get_id())          # load the user
    orders = ""                                   # prepare the string of orders of participants (their meals)
    for parti in u.participants.split():          # for each participant add his order to string of orders
        orders += parti + " : " + request.form[f"{parti}_meal"]+", "    # make it easy to convert it to dictionary latter

    orders += u.name + " : " + request.form[u.name+"_meal"]     # add the meal of admin, bc he isn't in the list of par.
    order = Order(request.form["wiot"])           # make the object of order + add attribute of who ordered
    order.restaurant = request.form["rest"]       # add restaurant
    order.time = request.form["time_of_order"]    # time
    order.orders = orders                         # orders of participants
    db_session.add(order)                         # add object
    db_session.commit()                           # write out changes
    flash("You've just made the order !","success")      # flash message about the order
    return redirect(url_for("account_page"))      # redirect back to account


# time configuration
@login_required
@app.route("/account/change_time/",methods=["POST"])
def change_time():
    new_time = request.form["time_from"] + " " + request.form["time_to"]    # unite times to one string
    u = load_user(current_user.get_id())                                    # get the actual user
    u.time = new_time                                                       # configure his new time settings
    db_session.commit()                                                     # commit changes
    return redirect(url_for("account_page"))                                # back to account


# participants configuration
@login_required
@app.route("/account/add_participant/",methods=["POST"])
def add_parti():
    u = load_user(current_user.get_id())                    # load the user
    u.participants += request.form["name"] + " "            # add participant to participants list
    db_session.commit()                                     # commit chnages
    return redirect(url_for("account_page"))                # back to the account page


@login_required
@app.route("/account/delete_participant/<name>/")
def delete_parti(name):
    u = load_user(current_user.get_id())                # load the user
    parti = u.participants.split()                      # make the list of participants from the string
    parti.remove(name)                                  # remove participant by name
    names = ' '.join([str(elem) for elem in parti])     # make the list string again
    u.participants = names                              # change the attribute of the User object
    db_session.commit()                                 # commit changes
    return redirect(url_for("account_page"))            # back to the account page


# restaurants configuration
@login_required
@app.route("/account/add_restaurant/",methods=["POST"])
def add_rest():
    u = load_user(current_user.get_id())                # same as participants
    u.restaurants += request.form["name-res"] + " "
    db_session.commit()
    return redirect(url_for("account_page"))


@login_required
@app.route("/account/delete_restaurants/<name>/")
def delete_rest(name):
    u = load_user(current_user.get_id())                # same as participants
    rest = u.restaurants.split()
    rest.remove(name)
    names = ' '.join([str(elem) for elem in rest])
    u.restaurants = names
    db_session.commit()
    return redirect(url_for("account_page"))


# load user from db
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == user_id).first()    # function to load user from the database by his id in session


@app.errorhandler(404)
def error404_fun(error):
    return render_template("404.html")                      # page for invalid url addresses


# closing connection with db
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.shell_context_processor
def make_shell_context():
    return dict(db="food_order.db", User=User, Order=Order)


if __name__ == "__main__":
    app.run(debug=True)

