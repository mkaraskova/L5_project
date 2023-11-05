from datetime import datetime

import bson
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import timedelta


app = Flask(__name__)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=14)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'Thisismysecretkey'

client = MongoClient(os.getenv('MONGO_DB'))
db = client["eMood"]
users = db["Users"]

csrf = CSRFProtect()
csrf.init_app(app)


class User(UserMixin):
    def __init__(self, name, email, hashed_password):
        self.name = name
        self.email = email
        self.password = hashed_password

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_name(self):
        return self.name

    def get_email(self):
        return self.email

    def get_id(self):
        return self.email


@login_manager.user_loader
def load_user(user_email):
    u = users.find_one({"email": user_email})
    if not u:
        return None
    return User(u['name'], u['email'], u['password'])


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    hashed_pwd = generate_password_hash(request.form['password'], method='sha256')

    new_user = {
        "_id": bson.ObjectId(),
        "name": request.form['name'],
        "email": request.form['email'],
        "password": hashed_pwd,
    }

    # Insert the new user into database
    # Make sure to handle the case where the user already exists
    if users.find_one({"email": new_user["email"]}):
        return 'Email already exists'
    else:
        users.insert_one(new_user)
        return 'User created!'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('profile'))
        else:
            return redirect(url_for('login.html'))

    email = request.form.get('email')
    password = request.form.get('password')
    user = load_user(email)  # get user from DB

    if user is None:
        return 'Email not found'
    elif not check_password_hash(user.password, password):
        return 'Email and password do not match'

    login_user(user, remember=True)
    return 'Login successful'


@app.route('/logout', methods=['GET', 'POST'])
def do_logout():
    logout_user()
    return render_template('login.html')


@app.route('/profile')
@login_required
def profile():
    user_data = {
        'name': current_user.name,
        'email': current_user.email,
    }
    return render_template('profile.html', user=user_data)


@app.route('/')
def root_redirect():
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)