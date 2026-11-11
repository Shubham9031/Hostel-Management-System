from flask import current_app
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

_client = None
_db = None

def init_db(app):
    global _client, _db
    try:
        _client = MongoClient(
            app.config['MONGO_URI'],
            serverSelectionTimeoutMS=5000
        )
        _client.admin.command('ping')
        _db = _client[app.config['DB_NAME']]
        _create_indexes(_db)
        app.logger.info("MongoDB connected successfully")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        app.logger.error(f"MongoDB connection failed: {e}")
        _db = None

def get_db():
    global _db
    if _db is None:
        raise ConnectionError("MongoDB is not running or MONGO_URI is wrong.")
    return _db

def _create_indexes(db):
    try:
        db.users.create_index([('username', ASCENDING)], unique=True)
        db.students.create_index([('roll_number', ASCENDING)], unique=True)
        db.rooms.create_index([('block_id', ASCENDING), ('room_number', ASCENDING)], unique=True)
        db.allocations.create_index([('student_id', ASCENDING), ('status', ASCENDING)])
        db.fees.create_index([('student_id', ASCENDING)])
        db.payments.create_index([('fee_id', ASCENDING)])
        db.complaints.create_index([('student_id', ASCENDING), ('status', ASCENDING)])
        db.leaves.create_index([('student_id', ASCENDING), ('status', ASCENDING)])
        db.notices.create_index([('created_at', ASCENDING)])
        db.visitors.create_index([('visit_date', ASCENDING)])
    except Exception:
        pass
