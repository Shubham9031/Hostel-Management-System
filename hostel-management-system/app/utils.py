from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from bson import ObjectId
from bson.errors import InvalidId

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def safe_object_id(id_str):
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        return None

def paginate(query_result, page, per_page=10):
    total = len(query_result)
    start = (page - 1) * per_page
    end = start + per_page
    items = query_result[start:end]
    total_pages = (total + per_page - 1) // per_page
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }
