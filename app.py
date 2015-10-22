#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from forms import LoginForm, AnswerForm, PriceForm
from flask.ext.login import LoginManager, login_user, login_required, UserMixin, logout_user, current_user
from hasher import gen_hash
from UserTools import User, generate_user_stats, get_display_name, get_user_points
from ProblemTools import display_problems_per_user, parseProblemFile, PROBLEM_FILE, categorize_problems
from RedisConf import HOSTNAME, PORT, USER_DB, PROBLEM_DB, COMMODITY_DB
import redis
import RedisConnect as rc
from  InitiateRedis import check_database_initiated
import logic as lg
from flask_conf import SECRET_KEY
from log_to_users import log_submission, log_purchase, log_on_market, log_changed_price

from werkzeug.contrib.fixers import ProxyFix

app = Flask(__name__)

app.secret_key = SECRET_KEY
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

user_pool = redis.ConnectionPool(host=HOSTNAME, port=PORT, db=USER_DB)
problem_pool = redis.ConnectionPool(host=HOSTNAME, port=PORT, db=PROBLEM_DB)

parsed_problem_file = parseProblemFile(PROBLEM_FILE)

app.wsgi_app = ProxyFix(app.wsgi_app)

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
    username = current_user.name
    user_stats = generate_user_stats(username, user_pool)

    info_to_render = {"user_info": user_stats, "table_info": display_problems_per_user(user_stats, parsed_problem_file)}

    return render_template('stats.html', info_to_render=info_to_render, logged_in_user=current_user)


@app.route('/problems')
@login_required
def problems():
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
            result, points = rc.submit_solution(submitted_answer, current_problem.name, problem_pool)
            if result:
                status = rc.update_user_solution(points, current_problem.name, current_user.name, user_pool)
                if not status:
                    return render_template('error_page.html', logged_in_user=current_user, error="Something went wrong. Try submitting your answer again.")
                else:
                    log_submission(current_user.name, current_problem.name, points)
                    return render_template('success_page.html', logged_in_user=current_user, message="Your answer was correct. You gained {0} points.".format(points))

    return render_template('submit_answer.html', form=form, error=error, logged_in_user=current_user, current_problem=current_problem)

@app.route('/solutions/sell/<problem_name>', methods=['GET', 'POST'])
@login_required
def put_solution_on_market(problem_name):
    current_problem = None
    error = None
    for name,problem in parsed_problem_file:
        if name == problem_name:
            current_problem = lg.Problem.fromString(problem)
            break

    if not current_problem:
        error = "You entered a URL for a non-existent problem."
        return render_template('error_page.html', logged_in_user=current_user, error=error)

    username = current_user.name
    user_stats = generate_user_stats(username, user_pool)

    categorized_problems = categorize_problems(user_stats, parsed_problem_file)

    if not problem_name in (name for name,_ in categorized_problems['to_sell']):
        error = "You have either already put up the solution for sale, or you have not solved the problem yet."
        return render_template('error_page.html', logged_in_user=current_user, error=error)

    if get_user_points(username, user_pool) < lg.MARKET_FEE_NEW_ITEM:
        error = "You don't have enough points to put up the solution on market."
        return render_template('error_page.html', logged_in_user=current_user, error=error)

    form = PriceForm(request.form)
    if request.method == 'POST':
        price_requested_str = request.form['price']
        try:
            price_requested = int(price_requested_str)
            if price_requested < 0:
                error = "The price must be a non-negative integer."
                return render_template('sale_page.html', form=form, error=error, logged_in_user=current_user, current_problem=current_problem, market_fee=lg.MARKET_FEE_NEW_ITEM)
            rc.sell_solution(current_user.name, current_problem.name, price_requested, user_pool)
            log_on_market(current_user.name, current_problem.name, price_requested, lg.MARKET_FEE_NEW_ITEM)
            return render_template('success_page.html', logged_in_user=current_user, message="You successfully put up the solution of {0} for the price of {1} points.".format(current_problem.display_name.lower(), price_requested))

        except ValueError:
            error = "The price must be a non-negative integer."
            return render_template('sale_page.html', form=form, error=error, logged_in_user=current_user, current_problem=current_problem, market_fee=lg.MARKET_FEE_NEW_ITEM)

    return render_template('sale_page.html', form=form, error=error, logged_in_user=current_user, current_problem=current_problem, market_fee=lg.MARKET_FEE_NEW_ITEM)

@app.route('/solutions/change_price/<problem_name>', methods=['GET', 'POST'])
@login_required
def change_solution_price(problem_name):
    current_problem = None
    error = None
    for name, problem in parsed_problem_file:
        if name == problem_name:
            current_problem = lg.Problem.fromString(problem)
            break

    if not current_problem:
        error = "You entered a URL for a non-existent problem."
        return render_template('error_page.html', logged_in_user=current_user, error=error)

    username = current_user.name
    user_stats = generate_user_stats(username, user_pool)

    categorized_problems = categorize_problems(user_stats, parsed_problem_file)

    if not problem_name in (name for name,_ in categorized_problems['on_market']):
        error = "You have not put this problem up on the market yet."
        return render_template('error_page.html', logged_in_user=current_user, error=error)

    if get_user_points(username, user_pool) < lg.MARKET_FEE_CHANGE_PRICE:
        error = "You don't have enough points to change the price of the solution."
        return render_template('error_page.html', logged_in_user=current_user, error=error)


    form = PriceForm(request.form)
    if request.method == 'POST':
        price_requested_str = request.form['price']
        try:
            price_requested = int(price_requested_str)
            if price_requested < 0:
                error = "The price must be a non-negative integer."
                return render_template('change_price.html', form=form, error=error, logged_in_user=current_user, current_problem=current_problem, market_fee=lg.MARKET_FEE_CHANGE_PRICE)
            result = rc.change_solution_price(current_user.name, current_problem.name, price_requested, user_pool, User.user_database)
            log_changed_price(current_user.name, current_problem.name, price_requested, lg.MARKET_FEE_CHANGE_PRICE)
            if result:
                return render_template('success_page.html', logged_in_user=current_user, message = "You successfully changed the price of the solution of {0} to {1} points.".format(current_problem.display_name.lower(), price_requested))
            else:
                return render_template('error_page.html', logged_in_user=current_user, error="Something wrong happened. Try again.")

        except ValueError:
            error = "The price must be a non-negative integer."
            return render_template('change_price.html', form=form, error=error, logged_in_user=current_user, current_problem=current_problem, market_fee=lg.MARKET_FEE_CHANGE_PRICE)

    return render_template('change_price.html', form=form, error=error, logged_in_user=current_user, current_problem=current_problem, market_fee=lg.MARKET_FEE_CHANGE_PRICE)

@app.route('/solutions/list/<problem_name>')
@login_required
def list_solutions_for_sale(problem_name):
    current_problem = None
    error = None
    for name,problem in parsed_problem_file:
        if name == problem_name:
            current_problem = lg.Problem.fromString(problem)
            break

    if not current_problem:
        return render_template('error_page.html', logged_in_user=current_user, error="You entered a URL for a non-existent problem.")

    username = current_user.name
    user_stats = generate_user_stats(username, user_pool)

    categorized_problems = categorize_problems(user_stats, parsed_problem_file)

    if not problem_name in (name for name,_ in categorized_problems['to_solve']):
        return render_template('error_page.html', logged_in_user=current_user, error="You have either already solved the problem, or you are not allowed to solve it.")

    all_commodities = rc.list_all_commodities(User.user_database, user_pool)
    problem_commodities = [(prob, user, get_display_name(user), price) for (prob, user, price) in all_commodities if prob == current_problem.name]
    return render_template('list_problems.html', logged_in_user=current_user, current_problem=current_problem, commodities=problem_commodities)

@app.route('/solutions/buy/<problem_name>/<seller_name>')
@login_required
def buy_solution(problem_name, seller_name):
    current_problem = None
    error = None
    for name,problem in parsed_problem_file:
        if name == problem_name:
            current_problem = lg.Problem.fromString(problem)
            break

    if not current_problem:
        return render_template('error_page.html', logged_in_user=current_user, error="You entered a URL for a non-existent problem.")

    username = current_user.name
    user_stats = generate_user_stats(username, user_pool)

    categorized_problems = categorize_problems(user_stats, parsed_problem_file)

    if not problem_name in (name for name,_ in categorized_problems["to_solve"]):
        return render_template('error_page.html', logged_in_user=current_user, error="You have either solved the problem or you are not allowed to access it yet.")

    all_commodities = rc.list_all_commodities(User.user_database, user_pool)
    found = False
    for prob,user,price_requested in all_commodities:
        if prob==problem_name and user==seller_name:
            found = True
            break
    if not found:
        error = "The seller is not selling the solution to this problem."
        return render_template('error_page.html', logged_in_user=current_user, error=error)

    if get_user_points(username, user_pool) < price_requested:
        error = "You don't have enough points to buy the solution to this problem."
        return render_template('error_page.html', logged_in_user=current_user, error=error)

    rc.pay_user(seller_name, price_requested, user_pool)
    rc.charge_user(current_user.name, price_requested, user_pool)
    result, points = rc.submit_solution(current_problem.answer, current_problem.name, problem_pool)
    if not result:
        error = "Something really bad happened."
        return render_template('error_page.html', logged_in_user=current_user, error=error)
    else:
        rc.update_user_solution(points, current_problem.name, current_user.name, user_pool)
        rc.add_to_purchases(current_user.name, current_problem.name, user_pool)
        log_purchase(current_user.name, seller_name, current_problem.name, price_requested, points)
        message = "You bought the solution of {0} from {1} at the price of {2} points.".format(current_problem.display_name.lower(), get_display_name(seller_name), price_requested)
        return render_template('success_page.html', logged_in_user=current_user, message=message)

"""
if __name__=="__main__":
    import sys
    if check_database_initiated(user_pool):
        app.run(host="0.0.0.0", debug=True)
    else:
        print("Users not initiated")
        sys.exit(1)
"""
