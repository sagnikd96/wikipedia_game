#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request, session, flash, g
from functools import wraps
import sqlite3
from forms import LoginForm, AnswerForm, SourceForm
from flask.ext.login import LoginManager, login_user, login_required, UserMixin, logout_user, current_user
from passwd import credentials
from hash_password import gen_hash

import os
from werkzeug import secure_filename

app = Flask(__name__)

app.secret_key = "my precious"
app.database = "sample.db"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

UPLOAD_FOLDER = '/tmp/'
ALLOWED_EXTENSIONS = ["txt", "pdf", "csv"]
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

class User(UserMixin):
    # proxy for a database of users
    user_database = {i:(i, credentials[i]) for i in credentials}

    def __init__(self, username, password_hash):
        self.id = username
        self.password_hash = password_hash

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            username = request.form['username']
            password = request.form['password']
            if (not username in User.user_database) or gen_hash(password) != User.get(username)[1]:
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
    #g.db = connect_db()
    #cur = g.db.execute("select * from posts")
    #posts = [dict(title=row[0], description=row[1]) for row in cur.fetchall()]
    #g.db.close()
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You were just logged out")
    return redirect(url_for('home'))

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def input_answer():
    form = AnswerForm(request.form)
    if form.validate_on_submit():
        answer = request.form["answer"]
        if gen_hash(answer) == current_user.password_hash:
            flash("Correct answer")
        else:
            flash("Boo! Wrong answer.")
        return render_template('console.html', form=form)
    return render_template('console.html', form=form)

@app.route('/source', methods=['GET', 'POST'])
@login_required
def source_submit():
    error = None
    form = SourceForm(request.form)
    if form.validate_on_submit():
        print(type(form.source.data))
        filename = secure_filename(form.source.data.filename)
        print(filename)
        if allowed_file(filename):
            form.source.data.save(UPLOAD_FOLDER+filename)
        else:
            error = "Not a valid filetype."
    return render_template('source_submit.html', form=form, error=error)

def connect_db():
    return sqlite3.connect(app.database)

if __name__=="__main__":
    app.run(debug=True)
