from flask_login import UserMixin
from bson import ObjectId
from .db import get_db
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.role = user_data['role']
        self.name = user_data.get('name', '')
        self.email = user_data.get('email', '')
        self._password_hash = user_data.get('password', '')

    @staticmethod
    def get_by_id(user_id):
        try:
            db = get_db()
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
        except Exception:
            return None
        return None

    @staticmethod
    def get_by_username(username):
        try:
            db = get_db()
            user_data = db.users.find_one({'username': username})
            if user_data:
                return User(user_data)
        except Exception:
            return None
        return None

    def check_password(self, password):
        return check_password_hash(self._password_hash, password)

    @staticmethod
    def create(username, password, role, name, email):
        db = get_db()
        user = {
            'username': username,
            'password': generate_password_hash(password),
            'role': role,
            'name': name,
            'email': email
        }
        result = db.users.insert_one(user)
        return str(result.inserted_id)
