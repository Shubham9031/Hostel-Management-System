from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from ..db import get_db
from ..utils import role_required, safe_object_id

leaves_bp = Blueprint('leaves', __name__, url_prefix='/leaves')

@leaves_bp.route('/')
@login_required
def index():
    try:
        db = get_db()
        if current_user.role in ['admin', 'warden']:
            status_filter = request.args.get('status', '')
            page = int(request.args.get('page', 1))
            per_page = 10
            query = {}
            if status_filter:
                query['status'] = status_filter
            leaves = list(db.leaves.find(query).sort('created_at', -1))
            result = []
            for lv in leaves:
                student = db.students.find_one({'_id': safe_object_id(lv.get('student_id', ''))})
                lv['student_name'] = student['name'] if student else 'Unknown'
                lv['student_roll'] = student.get('roll_number', '') if student else ''
                result.append(lv)
            total = len(result)
            total_pages = max(1, (total + per_page - 1) // per_page)
            paginated = result[(page-1)*per_page:page*per_page]
            return render_template('shared/leaves_list.html', leaves=paginated, status_filter=status_filter, page=page, total_pages=total_pages, total=total)
        else:
            student = db.students.find_one({'user_id': current_user.id})
            if not student:
                flash('Student profile not found.', 'warning')
                return render_template('shared/leaves_list.html', leaves=[], status_filter='', page=1, total_pages=1, total=0)
            leaves = list(db.leaves.find({'student_id': str(student['_id'])}).sort('created_at', -1))
            return render_template('shared/leaves_list.html', leaves=leaves, status_filter='', page=1, total_pages=1, total=len(leaves))
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/leaves_list.html', leaves=[], status_filter='', page=1, total_pages=1, total=0)

@leaves_bp.route('/apply', methods=['GET', 'POST'])
@login_required
@role_required('student')
def apply():
    if request.method == 'POST':
        try:
            db = get_db()
            student = db.students.find_one({'user_id': current_user.id})
            if not student:
                flash('Student profile not found.', 'danger')
                return redirect(url_for('dashboard.index'))
            from_date = request.form.get('from_date', '').strip()
            to_date = request.form.get('to_date', '').strip()
            reason = request.form.get('reason', '').strip()
            leave_type = request.form.get('leave_type', 'Leave')
            if not all([from_date, to_date, reason]):
                flash('All fields are required.', 'danger')
                return render_template('shared/leave_form.html')
            db.leaves.insert_one({
                'student_id': str(student['_id']), 'from_date': from_date,
                'to_date': to_date, 'reason': reason, 'leave_type': leave_type,
                'status': 'Pending', 'remarks': '', 'created_at': datetime.now()
            })
            flash('Leave application submitted.', 'success')
            return redirect(url_for('leaves.index'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('shared/leave_form.html')

@leaves_bp.route('/review/<leave_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def review(leave_id):
    db = get_db()
    oid = safe_object_id(leave_id)
    if not oid:
        flash('Invalid leave ID.', 'danger')
        return redirect(url_for('leaves.index'))
    leave = db.leaves.find_one({'_id': oid})
    if not leave:
        flash('Leave not found.', 'danger')
        return redirect(url_for('leaves.index'))
    if request.method == 'POST':
        status = request.form.get('status', 'Pending')
        remarks = request.form.get('remarks', '').strip()
        db.leaves.update_one({'_id': oid}, {'$set': {'status': status, 'remarks': remarks, 'reviewed_at': datetime.now(), 'reviewed_by': current_user.id}})
        flash(f'Leave application {status.lower()}.', 'success')
        return redirect(url_for('leaves.index'))
    student = db.students.find_one({'_id': safe_object_id(leave.get('student_id', ''))})
    return render_template('shared/leave_review.html', leave=leave, student=student)
