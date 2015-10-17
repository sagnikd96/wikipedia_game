#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from forms import LoginForm, AnswerForm
from flask.ext.login import LoginManager, login_user, login_required, UserMixin, logout_user, current_user
from hasher import gen_hash
from UserTools import User, generate_user_stats
from ProblemTools import display_problems_per_user, parseProblemFile, PROBLEM_FILE, categorize_problems
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
    return render_template('index.html', display_name=display_name, logged_in_user=current_user)

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
    parsed_problem_file = parseProblemFile(PROBLEM_FILE)

    username = current_user.name
    user_stats = generate_user_stats(username, user_pool)

    info_to_render = {"user_info": user_stats, "table_info": display_problems_per_user(user_stats, parsed_problem_file)}

    return render_template('stats.html', info_to_render=info_to_render, logged_in_user=current_user)


@app.route('/problems')
@login_required
def problems():
    parsed_problem_file = parseProblemFile(PROBLEM_FILE)

    username = current_user.name
    user_stats = generate_user_stats(username, user_pool)

    categorized_problems = categorize_problems(user_stats, parsed_problem_file)
    #return str(categorized_problems)
    return render_template('problems.html', categorized_problems=categorized_problems, logged_in_user=current_user)

@app.route('/problems/submit/<prob_name>', methods=['GET', 'POST'])
@login_required
def post_solution(prob_name):
    current_problem = None
    error = None
    parsed_problem_file = parseProblemFile(PROBLEM_FILE)
    for name,problem in parsed_problem_file:
        if name == prob_name:
            current_problem = lg.Problem.fromString(problem)
            break

    if not current_problem:
        return render_template('error_page.html', logged_in_user=current_user, error="You entered a URL for a non-existent problem.")

    username = current_user.name
    user_stats = generate_user_stats(username, user_pool)

    categorized_problems = categorize_problems(user_stats, parsed_problem_file)

    if not prob_name in (name for name,_ in categorized_problems["to_solve"]):
        return render_template('error_page.html', logged_in_user=current_user, error="You have either solved the problem or you are not allowed to solve it.")

    form = AnswerForm(request.form)
    if request.method == 'POST':
        submitted_answer = request.form['answer']
        if submitted_answer != current_problem.answer:
            if not submitted_answer:
                error = "Enter an answer"
            else:
                error = "Wrong answer. Try again."
            return render_template('submit_answer.html', form=form, error=error, logged_in_user=current_user, current_problem=current_problem)
        else:
            return "Correcto"
    return render_template('submit_answer.html', form=form, error=error, logged_in_user=current_user, current_problem=current_problem)

if __name__=="__main__":
    import sys
    if check_database_initiated(user_pool):
        app.run(host="0.0.0.0", debug=True)
    else:
        print("Users not initiated")
        sys.exit(1)
