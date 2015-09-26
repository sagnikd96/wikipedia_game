#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from functools import wraps
import sqlite3
from forms import LoginForm
from flask.ext.login import LoginManager, login_user, login_required, UserMixin, logout_user

app = Flask(__name__)

app.secret_key = "my precious"
app.database = "sample.db"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    # proxy for a database of users
    user_database = {"JohnDoe": ("JohnDoe", "John"),
               "JaneDoe": ("JaneDoe", "Jane")}

    def __init__(self, username, password):
        self.id = username
        self.password = password

    @classmethod
    def get(cls,idd):
        return cls.user_database.get(idd)


@login_manager.user_loader
def load_user(user_id):
    result = User.get(user_id)
    if result:
        return User(result[0], result[1])
    else:
        return None

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
            username = request.form['username']
            password = request.form['password']
            if (not username in User.user_database) or password != User.get(username)[1]:
                error = "Invalid Creds. Try again."
            else:
                login_user(load_user(username))
                flash("You were just logged in")
                return redirect(url_for('welcome'))
        else:
            return render_template("login.html", form=form, error=error)
    return render_template('login.html', form=form, error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You were just logged out")
    return redirect(url_for('home'))

def connect_db():
    return sqlite3.connect(app.database)

if __name__=="__main__":
    app.run(debug=True)
