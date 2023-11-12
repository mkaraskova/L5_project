from flask import Flask, request, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf
from fer import FER
import bson
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import timedelta, datetime

app = Flask(__name__)
detector = FER(mtcnn=False)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=14)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'Thisismysecretkey'

client = MongoClient(os.getenv('MONGO_DB'))
db = client["eMood"]
users = db["Users"]
webpages = db["Webpages"]

csrf = CSRFProtect()
csrf.init_app(app)


class User(UserMixin):
    def __init__(self, name, email, gender, hashed_password):
        self.name = name
        self.email = email
        self.gender = gender
        self.password = hashed_password

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_name(self):
        return self.name

    def get_email(self):
        return self.email

    def get_id(self):
        return self.email


def update_profile(user_id, update_fields):
    users.update_one(
        {"email": user_id},
        {"$set": update_fields}
    )


@login_manager.user_loader
def load_user(user_email):
    u = users.find_one({"email": user_email})
    if u is None:
        return None
    if 'gender' not in u:
        u['gender'] = 'N/A'
    return User(u['name'], u['email'], u['gender'], u['password'])


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    hashed_pwd = generate_password_hash(request.form['password'], method='sha256')

    new_user = {
        "_id": bson.ObjectId(),
        "name": request.form['name'],
        "email": request.form['email'],
        "gender": "N/A",
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
            return render_template('login.html')

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
        'gender': current_user.gender,
    }

    return render_template('profile.html', user=user_data)


@app.route('/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')
    gender = request.form.get('gender')

    update_fields = {}

    if name:
        update_fields["name"] = name
    if email:
        update_fields["email"] = email
    if gender:
        update_fields["gender"] = gender

    update_profile(current_user.email, update_fields)
    return redirect(url_for('profile'))


@app.route('/webpage', methods=["POST"])
def detect_url():
    data = request.get_json()
    urls = data['urls']
    current_timestamp = datetime.now()
    if urls:
        webpages.insert_one({
            "urls": urls,
            "timestamp": current_timestamp
        })
        response = jsonify('Urls added successfully!')
        response.status_code = 200
        return response
    else:
        return not_found()


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp


@app.route('/get-csrf-token')
def csrf_token():
    token = generate_csrf()
    return jsonify({"csrf_token": token})


@app.route('/')
def root_redirect():
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
