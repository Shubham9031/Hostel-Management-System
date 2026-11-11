from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from bson import ObjectId
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from ..db import get_db
from ..utils import role_required, safe_object_id
from werkzeug.security import generate_password_hash

students_bp = Blueprint('students', __name__, url_prefix='/students')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@students_bp.route('/')
@login_required
@role_required('admin', 'warden')
def index():
    try:
        db = get_db()
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = 10
        query = {}
        if search:
            query = {'$or': [
                {'name': {'$regex': search, '$options': 'i'}},
                {'roll_number': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}}
            ]}
        total = db.students.count_documents(query)
        students = list(db.students.find(query).skip((page-1)*per_page).limit(per_page))
        total_pages = (total + per_page - 1) // per_page
        return render_template('shared/students_list.html', students=students, search=search,
            page=page, total_pages=total_pages, total=total)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/students_list.html', students=[], search='', page=1, total_pages=1, total=0)

@students_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def add():
    if request.method == 'POST':
        try:
            db = get_db()
            name = request.form.get('name', '').strip()
            roll_number = request.form.get('roll_number', '').strip()
            course = request.form.get('course', '').strip()
            year = request.form.get('year', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            guardian_name = request.form.get('guardian_name', '').strip()
            guardian_phone = request.form.get('guardian_phone', '').strip()
            address = request.form.get('address', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            if not all([name, roll_number, course, year, phone, email, username, password]):
                flash('All required fields must be filled.', 'danger')
                return render_template('shared/student_form.html', student=None, action='Add')
            if db.students.find_one({'roll_number': roll_number}):
                flash('Roll number already exists.', 'danger')
                return render_template('shared/student_form.html', student=None, action='Add')
            if db.users.find_one({'username': username}):
                flash('Username already taken.', 'danger')
                return render_template('shared/student_form.html', student=None, action='Add')
            photo_filename = None
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename and allowed_file(photo.filename):
                    from flask import current_app
                    filename = secure_filename(f"{roll_number}_{photo.filename}")
                    photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    photo_filename = filename
            user_id = str(db.users.insert_one({
                'username': username, 'password': generate_password_hash(password),
                'role': 'student', 'name': name, 'email': email
            }).inserted_id)
            student_data = {
                'user_id': user_id, 'name': name, 'roll_number': roll_number,
                'course': course, 'year': year, 'phone': phone, 'email': email,
                'guardian_name': guardian_name, 'guardian_phone': guardian_phone,
                'address': address, 'photo': photo_filename, 'status': 'Active',
                'created_at': datetime.now()
            }
            db.students.insert_one(student_data)
            flash(f'Student {name} added successfully. Login: {username} / {password}', 'success')
            return redirect(url_for('students.index'))
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'danger')
    return render_template('shared/student_form.html', student=None, action='Add')

@students_bp.route('/edit/<student_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def edit(student_id):
    db = get_db()
    oid = safe_object_id(student_id)
    if not oid:
        flash('Invalid student ID.', 'danger')
        return redirect(url_for('students.index'))
    student = db.students.find_one({'_id': oid})
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.index'))
    if request.method == 'POST':
        try:
            update_data = {
                'name': request.form.get('name', '').strip(),
                'course': request.form.get('course', '').strip(),
                'year': request.form.get('year', '').strip(),
                'phone': request.form.get('phone', '').strip(),
                'email': request.form.get('email', '').strip(),
                'guardian_name': request.form.get('guardian_name', '').strip(),
                'guardian_phone': request.form.get('guardian_phone', '').strip(),
                'address': request.form.get('address', '').strip(),
                'status': request.form.get('status', 'Active')
            }
            if not all([update_data['name'], update_data['course'], update_data['year'], update_data['phone'], update_data['email']]):
                flash('Required fields missing.', 'danger')
                return render_template('shared/student_form.html', student=student, action='Edit')
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename and allowed_file(photo.filename):
                    from flask import current_app
                    filename = secure_filename(f"{student['roll_number']}_{photo.filename}")
                    photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    update_data['photo'] = filename
            db.students.update_one({'_id': oid}, {'$set': update_data})
            if student.get('user_id'):
                db.users.update_one({'_id': ObjectId(student['user_id'])}, {'$set': {'name': update_data['name'], 'email': update_data['email']}})
            flash('Student updated successfully.', 'success')
            return redirect(url_for('students.index'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('shared/student_form.html', student=student, action='Edit')

@students_bp.route('/delete/<student_id>', methods=['POST'])
@login_required
@role_required('admin', 'warden')
def delete(student_id):
    db = get_db()
    oid = safe_object_id(student_id)
    if not oid:
        flash('Invalid student ID.', 'danger')
        return redirect(url_for('students.index'))
    student = db.students.find_one({'_id': oid})
    if student:
        if student.get('user_id'):
            db.users.delete_one({'_id': ObjectId(student['user_id'])})
        db.students.delete_one({'_id': oid})
        flash('Student deleted successfully.', 'success')
    else:
        flash('Student not found.', 'danger')
    return redirect(url_for('students.index'))

@students_bp.route('/view/<student_id>')
@login_required
def view(student_id):
    db = get_db()
    oid = safe_object_id(student_id)
    if not oid:
        flash('Invalid student ID.', 'danger')
        return redirect(url_for('students.index'))
    student = db.students.find_one({'_id': oid})
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.index'))
    allocation = db.allocations.find_one({'student_id': student_id, 'status': 'Active'})
    room = None
    block = None
    if allocation:
        room = db.rooms.find_one({'_id': safe_object_id(allocation['room_id'])})
        if room:
            block = db.blocks.find_one({'_id': safe_object_id(room['block_id'])})
    fees = list(db.fees.find({'student_id': student_id}))
    complaints = list(db.complaints.find({'student_id': student_id}).sort('created_at', -1).limit(5))
    leaves = list(db.leaves.find({'student_id': student_id}).sort('created_at', -1).limit(5))
    return render_template('shared/student_detail.html', student=student, allocation=allocation, room=room, block=block, fees=fees, complaints=complaints, leaves=leaves)
