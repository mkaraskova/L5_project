from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'Thisismysecretkey'

client = MongoClient(os.getenv('MONGO_DB'))
db = client["eMood"]
users = db["Users"]


class User(UserMixin):
    def __init__(self, email, hashed_password):
        self.email = email
        self.password = hashed_password

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_email(self):
        return self.email

    def get_id(self):
        return self.email


@login_manager.user_loader
def load_user(user_email):
    u = users.find_one({"_id": user_email})
    if not u:
        return None
    return User(u['_id'], u['password'])


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    hashed_pwd = generate_password_hash(request.form['password'], method='sha256')
    new_user = {
        "_id": request.form['email'],
        "password": hashed_pwd
    }

    # Insert the new user into database
    # Make sure to handle the case where the user already exists
    if users.find_one({"_id": new_user["_id"]}):
        return 'Email already exists'
    else:
        users.insert_one(new_user)
        return 'User created!'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    user = users.find_one({"_id": request.form['email']})

    if user and User(user['_id'], user['password']).check_password(request.form['password']):
        user_obj = User(user['_id'], user['password'])
        login_user(user_obj)
        return redirect(url_for('protected'))

    return 'Bad Login'


@app.route('/protected')
@login_required
def protected():
    return 'Logged in as: ' + current_user.get_email()


@app.route('/')
def root_redirect():
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
