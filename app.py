#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from forms import LoginForm, AnswerForm
from flask.ext.login import LoginManager, login_user, login_required, UserMixin, logout_user, current_user
from hasher import gen_hash
from UserTools import User
from RedisConf import HOSTNAME, PORT, USER_DB, PROBLEM_DB, COMMODITY_DB
import redis
import RedisConnect as rc
from  InitiateRedis import check_database_initiated

app = Flask(__name__)

app.secret_key = "my precious"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

user_pool = redis.ConnectionPool(host=HOSTNAME, port=PORT, db=USER_DB)
problem_pool = redis.ConnectionPool(host=HOSTNAME, port=PORT, db=PROBLEM_DB)
commodity_pool = redis.ConnectionPool(host=HOSTNAME, port=PORT, db=COMMODITY_DB)

@login_manager.user_loader
def load_user(user_id):
    result = User.get(user_id)
    if result:
        name, display_name, password_hash = User.user_database[user_id]
        return User(name, display_name, password_hash)
    else:
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            username = request.form['username']
            password = request.form['password']
            if (not username in User.user_database) or gen_hash(password) != User.get_password_hash(username):
                error = "Invalid Credentials. Try again."
            else:
                login_user(load_user(username))
                flash("You were just logged in")
                return redirect(url_for('home'))
        else:
            return render_template("login.html", form=form, error=error)
    return render_template('login.html', form=form, error=error)

@app.route('/')
@login_required
def home():
    display_name = current_user.display_name
    return render_template('index.html', display_name=display_name)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/scores')
def show_scores():
    users = [(user,User.user_database[user][1]) for user in User.user_database]
    users_info = []
    for user, display_name in users:
        try:
            user_info = rc.get_user_from_redis(user, user_pool)
            users_info.append((user, display_name, user_info[1]))
        except TypeError:
            pass
    if current_user.is_anonymous:
        return render_template('scores.html', scores=users_info)
    else:
        return render_template('scores.html', scores=users_info, logged_in_user=current_user)

if __name__=="__main__":
    import sys
    if check_database_initiated(user_pool):
        app.run(host="0.0.0.0", debug=True)
    else:
        print("Users not initiated")
        sys.exit(1)
