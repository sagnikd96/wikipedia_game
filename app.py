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
import logic as lg

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
            users_info.append((user, display_name, lg.UserLogic.scoreFromTuple(user_info), len(user_info[5])))
        except TypeError:
            pass
    users_info.sort(key=lambda x: x[2], reverse=True)
    positions = enumerate(users_info)
    if current_user.is_anonymous:
        return render_template('scores.html', scores=positions)
    else:
        return render_template('scores.html', scores=positions, logged_in_user=current_user)

@app.route('/stats')
@login_required
def stats():
    username = current_user.name
    user_info = rc.get_user_from_redis(username, user_pool)
    user_stats = {}
    user_stats['display_name'] = User.user_database[username][1]
    user_stats['current_points'] = lg.UserLogic.scoreFromTuple(user_info)
    user_stats['starting_points'] = user_info[1]
    user_stats['points_for_solving'] = user_info[2]
    user_stats['points_for_selling'] = user_info[3]
    user_stats['expenditure'] = user_info[4]

    problems_solved_dict = {}

    for problem in user_info[5]:
        problems_solved_dict[problem] = rc.get_problem_from_redis(problem, problem_pool).display_name

    user_stats['problems_solved'] = [problems_solved_dict[i] for i in problems_solved_dict]
    user_stats['solutions_bought'] = [problems_solved_dict[i] for i in user_info[6]]
    user_stats['solutions_sold'] = [problems_solved_dict[i] for i in user_info[7]]

    return str(user_stats)


@app.route('/problems')
@login_required
def problems():
    return "In progress"

@app.route('/market_console')
@login_required
def market_console():
    return "In progress"

if __name__=="__main__":
    import sys
    if check_database_initiated(user_pool):
        app.run(host="0.0.0.0", debug=True)
    else:
        print("Users not initiated")
        sys.exit(1)
