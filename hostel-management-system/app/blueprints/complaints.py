from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from ..db import get_db
from ..utils import role_required, safe_object_id

complaints_bp = Blueprint('complaints', __name__, url_prefix='/complaints')

@complaints_bp.route('/')
@login_required
def index():
    try:
        db = get_db()
        if current_user.role in ['admin', 'warden']:
            search = request.args.get('search', '')
            status_filter = request.args.get('status', '')
            page = int(request.args.get('page', 1))
            per_page = 10
            query = {}
            if status_filter:
                query['status'] = status_filter
            complaints = list(db.complaints.find(query).sort('created_at', -1))
            result = []
            for c in complaints:
                student = db.students.find_one({'_id': safe_object_id(c.get('student_id', ''))})
                if search and student:
                    if search.lower() not in student.get('name', '').lower():
                        continue
                c['student_name'] = student['name'] if student else 'Unknown'
                result.append(c)
            total = len(result)
            total_pages = max(1, (total + per_page - 1) // per_page)
            paginated = result[(page-1)*per_page:page*per_page]
            return render_template('shared/complaints_list.html', complaints=paginated, search=search, status_filter=status_filter, page=page, total_pages=total_pages, total=total)
        else:
            student = db.students.find_one({'user_id': current_user.id})
            if not student:
                flash('Student profile not found.', 'warning')
                return render_template('shared/complaints_list.html', complaints=[], search='', status_filter='', page=1, total_pages=1, total=0)
            complaints = list(db.complaints.find({'student_id': str(student['_id'])}).sort('created_at', -1))
            return render_template('shared/complaints_list.html', complaints=complaints, search='', status_filter='', page=1, total_pages=1, total=len(complaints))
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/complaints_list.html', complaints=[], search='', status_filter='', page=1, total_pages=1, total=0)

@complaints_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            db = get_db()
            category = request.form.get('category', '').strip()
            description = request.form.get('description', '').strip()
            if not all([category, description]):
                flash('Category and description are required.', 'danger')
                return render_template('shared/complaint_form.html', complaint=None, action='Add')
            if current_user.role == 'student':
                student = db.students.find_one({'user_id': current_user.id})
                student_id = str(student['_id']) if student else None
            else:
                student_id = request.form.get('student_id', '').strip()
            db.complaints.insert_one({
                'student_id': student_id, 'category': category,
                'description': description, 'status': 'Open',
                'remarks': '', 'created_at': datetime.now()
            })
            flash('Complaint submitted successfully.', 'success')
            return redirect(url_for('complaints.index'))
        except Exception as e:
            flash(str(e), 'danger')
    db = get_db()
    students = list(db.students.find({'status': 'Active'})) if current_user.role in ['admin', 'warden'] else []
    return render_template('shared/complaint_form.html', complaint=None, action='Add', students=students)

@complaints_bp.route('/update/<complaint_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def update(complaint_id):
    db = get_db()
    oid = safe_object_id(complaint_id)
    if not oid:
        flash('Invalid complaint ID.', 'danger')
        return redirect(url_for('complaints.index'))
    complaint = db.complaints.find_one({'_id': oid})
    if not complaint:
        flash('Complaint not found.', 'danger')
        return redirect(url_for('complaints.index'))
    if request.method == 'POST':
        status = request.form.get('status', 'Open')
        remarks = request.form.get('remarks', '').strip()
        db.complaints.update_one({'_id': oid}, {'$set': {'status': status, 'remarks': remarks, 'updated_at': datetime.now()}})
        flash('Complaint updated successfully.', 'success')
        return redirect(url_for('complaints.index'))
    student = db.students.find_one({'_id': safe_object_id(complaint.get('student_id', ''))})
    return render_template('shared/complaint_update.html', complaint=complaint, student=student)
