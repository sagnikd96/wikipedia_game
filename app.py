#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from functools import wraps
import sqlite3
from forms import LoginForm
from flask.ext.login import LoginManager, login_user, login_required

app = Flask(__name__)

app.secret_key = "my precious"
app.database = "sample.db"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"

class User():
    def __init__(self, idd):
        is_authenticated = False
        is_active = True
        is_anonymous = False
        id_num = idd

    def get_id(self):
        return id_num

    def authenticate(self):
        is_authenticated = True

    def unauthenticate(self):
        is_authenticated = False

"""
# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap
"""

@app.route('/')
@login_required
def home():
    g.db = connect_db()
    cur = g.db.execute("select * from posts")
    posts = [dict(title=row[0], description=row[1]) for row in cur.fetchall()]
    g.db.close()
    return render_template('index.html', posts=posts)

@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            if request.form['username'] != 'admin' or request.form['password'] != 'admin':
                error = 'Invalid Creds. Try again.'
            else:
                #session['logged_in'] = True
                login_user(User("admin"))
                flash("You were just logged in")
                return redirect(url_for('welcome'))
        else:
            return render_template("login.html", form=form, error=error)
    return render_template('login.html', form=form, error=error)

@login_manager.user_loader
def load_user(user_id):
    return "admin"

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash("You were just logged out")
    return redirect(url_for('home'))

def connect_db():
    return sqlite3.connect(app.database)

if __name__=="__main__":
    app.run(debug=True)
