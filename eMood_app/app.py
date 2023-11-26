import io
import json
import shutil
import uuid
from flask import send_file
import subprocess
from flask import Flask, request, jsonify, send_from_directory
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

from helpers import *

app = Flask(__name__)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=14)
app.config['SECRET_KEY'] = 'Thisismysecretkey'  # to be changed

login_manager = LoginManager()
login_manager.init_app(app)

# Initialize MongoDB client and collections
client = MongoClient(os.getenv('MONGO_DB'))
db = client["eMood"]
users = db["Users"]
webpages = db["Webpages"]
moods = db["Moods"]
monitored_users = db["MonitoredUsers"]

detector = FER(mtcnn=False)

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
            return redirect(url_for('dashboard'))
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


@app.route('/dashboard')
@login_required
def dashboard():
    monitored_users_list = monitored_users.find({"creator": current_user.email})
    return render_template('dashboard.html', monitored_users=monitored_users_list)


@app.route('/dashboard/<user_name>')
@login_required
def user_dashboard(user_name):
    user_details = monitored_users.find_one({"name": user_name, "creator": current_user.email})
    if user_details:
        user_id = user_details['userId']
        user_moods = list(moods.find({"userId": user_id}))
        if user_moods:
            [mood.pop('_id') for mood in user_moods]
        user_webpages = list(webpages.find({"userId": user_id}))
        if user_webpages:
            [webpage.pop('_id') for webpage in user_webpages]
        user_info = {
            "name": user_details['name'],
            "moods": user_moods,
            "webpages": user_webpages
        }
        return jsonify(user_info)


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
    user_id = data.get('userId')
    urls = data['urls']
    current_timestamp = datetime.now()
    if urls:
        webpages.insert_one({
            "userId": user_id,
            "urls": urls[0],  # only logs the active web page
            "timestamp": current_timestamp
        })
        response = jsonify('Urls added successfully!')
        response.status_code = 200
        return response
    else:
        return not_found()


@app.route('/add-person', methods=["POST"])
def add_person():
    name = request.form.get('name')
    user_id = str(uuid.uuid4())
    creator = current_user.email

    # Create a BytesIO object to hold the ZIP file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zipf:
        # add plugin files
        for file in os.listdir('eMood_app/eMood_plugin'):
            file_path = os.path.join('eMood_app/eMood_plugin', file)
            if os.path.isfile(file_path):
                zipf.write(file_path, arcname=os.path.join(f"eMood_plugin_{name}", file))

        # add detector executable
        file_path = os.path.join('eMood_app', 'eMood_detector', 'emotion_detector.py')
        mongo_connection = os.getenv('MONGO_DB')

        with open('eMood_app/eMood_detector/settings.json', 'w') as settings_file:
            json.dump({
                'userId': user_id,
                'mongoConnection': mongo_connection
            }, settings_file)

        # add plugin files
        for file in os.listdir('eMood_app/eMood_detector'):
            file_path = os.path.join('eMood_app/eMood_detector', file)
            if os.path.isfile(file_path):
                zipf.write(file_path, arcname=os.path.join(f"eMood_detector_{name}", file))

        # Add userid.txt to plugin
        zipf.writestr(f"eMood_plugin_{name}/userid.txt", user_id.encode('utf-8'))

    # Reset the buffer position to the beginning
    zip_buffer.seek(0)

    monitored_users.insert_one({"userId": user_id, "creator": creator, "name": name})

    # Return the generated ZIP file as a Flask response without saving it locally
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"eMood_plugin_{name}.zip"
    )


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
