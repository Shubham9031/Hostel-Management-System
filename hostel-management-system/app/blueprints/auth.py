from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from ..models import User
from ..db import get_db
from ..utils import role_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/login.html')
        try:
            user = User.get_by_username(username)
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(next_page or url_for('dashboard.index'))
            else:
                flash('Invalid username or password.', 'danger')
        except ConnectionError as e:
            flash(str(e), 'danger')
            return render_template('shared/db_error.html')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required.', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
        elif len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        else:
            try:
                user = User.get_by_username(current_user.username)
                if user and user.check_password(current_password):
                    db = get_db()
                    from bson import ObjectId
                    db.users.update_one(
                        {'_id': ObjectId(current_user.id)},
                        {'$set': {'password': generate_password_hash(new_password)}}
                    )
                    flash('Password changed successfully.', 'success')
                    return redirect(url_for('dashboard.index'))
                else:
                    flash('Current password is incorrect.', 'danger')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
    return render_template('auth/change_password.html')
