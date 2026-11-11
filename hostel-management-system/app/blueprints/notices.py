from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from ..db import get_db
from ..utils import role_required, safe_object_id

notices_bp = Blueprint('notices', __name__, url_prefix='/notices')

@notices_bp.route('/')
@login_required
def index():
    try:
        db = get_db()
        notices = list(db.notices.find().sort('created_at', -1))
        return render_template('shared/notices_list.html', notices=notices)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/notices_list.html', notices=[])

@notices_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def add():
    if request.method == 'POST':
        try:
            db = get_db()
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            priority = request.form.get('priority', 'Normal')
            if not all([title, content]):
                flash('Title and content are required.', 'danger')
                return render_template('shared/notice_form.html', notice=None, action='Add')
            db.notices.insert_one({
                'title': title, 'content': content, 'priority': priority,
                'posted_by': current_user.name, 'created_at': datetime.now()
            })
            flash('Notice posted successfully.', 'success')
            return redirect(url_for('notices.index'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('shared/notice_form.html', notice=None, action='Add')

@notices_bp.route('/edit/<notice_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def edit(notice_id):
    db = get_db()
    oid = safe_object_id(notice_id)
    if not oid:
        flash('Invalid notice ID.', 'danger')
        return redirect(url_for('notices.index'))
    notice = db.notices.find_one({'_id': oid})
    if not notice:
        flash('Notice not found.', 'danger')
        return redirect(url_for('notices.index'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'Normal')
        if not all([title, content]):
            flash('Title and content are required.', 'danger')
            return render_template('shared/notice_form.html', notice=notice, action='Edit')
        db.notices.update_one({'_id': oid}, {'$set': {'title': title, 'content': content, 'priority': priority, 'updated_at': datetime.now()}})
        flash('Notice updated.', 'success')
        return redirect(url_for('notices.index'))
    return render_template('shared/notice_form.html', notice=notice, action='Edit')

@notices_bp.route('/delete/<notice_id>', methods=['POST'])
@login_required
@role_required('admin', 'warden')
def delete(notice_id):
    db = get_db()
    oid = safe_object_id(notice_id)
    if oid:
        db.notices.delete_one({'_id': oid})
        flash('Notice deleted.', 'success')
    return redirect(url_for('notices.index'))
