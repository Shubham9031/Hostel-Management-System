from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from ..db import get_db
from ..utils import role_required

mess_bp = Blueprint('mess', __name__, url_prefix='/mess')
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

@mess_bp.route('/')
@login_required
def menu():
    try:
        db = get_db()
        menu_items = {day: {'breakfast': '', 'lunch': '', 'dinner': ''} for day in DAYS}
        for item in db.mess_menu.find():
            day = item.get('day')
            if day in menu_items:
                menu_items[day]['breakfast'] = item.get('breakfast', '')
                menu_items[day]['lunch'] = item.get('lunch', '')
                menu_items[day]['dinner'] = item.get('dinner', '')
        today = datetime.now().strftime('%A')
        return render_template('shared/mess_menu.html', menu=menu_items, days=DAYS, today=today)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/mess_menu.html', menu={}, days=DAYS, today='')

@mess_bp.route('/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def edit_menu():
    db = get_db()
    if request.method == 'POST':
        try:
            for day in DAYS:
                breakfast = request.form.get(f'{day}_breakfast', '').strip()
                lunch = request.form.get(f'{day}_lunch', '').strip()
                dinner = request.form.get(f'{day}_dinner', '').strip()
                db.mess_menu.update_one(
                    {'day': day},
                    {'$set': {'day': day, 'breakfast': breakfast, 'lunch': lunch, 'dinner': dinner}},
                    upsert=True
                )
            flash('Mess menu updated successfully.', 'success')
            return redirect(url_for('mess.menu'))
        except Exception as e:
            flash(str(e), 'danger')
    menu_items = {day: {'breakfast': '', 'lunch': '', 'dinner': ''} for day in DAYS}
    for item in db.mess_menu.find():
        day = item.get('day')
        if day in menu_items:
            menu_items[day] = item
    return render_template('shared/mess_edit.html', menu=menu_items, days=DAYS)

@mess_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def attendance():
    db = get_db()
    today = date.today().isoformat()
    if request.method == 'POST':
        try:
            attend_date = request.form.get('date', today)
            meal_type = request.form.get('meal_type', 'breakfast')
            present_ids = request.form.getlist('present_students')
            students = list(db.students.find({'status': 'Active'}))
            for student in students:
                sid = str(student['_id'])
                is_present = sid in present_ids
                db.meal_attendance.update_one(
                    {'student_id': sid, 'date': attend_date, 'meal_type': meal_type},
                    {'$set': {'student_id': sid, 'date': attend_date, 'meal_type': meal_type, 'present': is_present}},
                    upsert=True
                )
            flash('Attendance recorded.', 'success')
            return redirect(url_for('mess.attendance'))
        except Exception as e:
            flash(str(e), 'danger')
    students = list(db.students.find({'status': 'Active'}))
    attendance_date = request.args.get('date', today)
    meal_type = request.args.get('meal_type', 'breakfast')
    existing = {a['student_id']: a['present'] for a in db.meal_attendance.find({'date': attendance_date, 'meal_type': meal_type})}
    return render_template('shared/mess_attendance.html', students=students, attendance_date=attendance_date, meal_type=meal_type, existing=existing, today=today)

@mess_bp.route('/summary')
@login_required
@role_required('admin', 'warden')
def summary():
    try:
        db = get_db()
        month = request.args.get('month', datetime.now().strftime('%Y-%m'))
        students = list(db.students.find({'status': 'Active'}))
        result = []
        for student in students:
            sid = str(student['_id'])
            breakfast_count = db.meal_attendance.count_documents({'student_id': sid, 'date': {'$regex': f'^{month}'}, 'meal_type': 'breakfast', 'present': True})
            lunch_count = db.meal_attendance.count_documents({'student_id': sid, 'date': {'$regex': f'^{month}'}, 'meal_type': 'lunch', 'present': True})
            dinner_count = db.meal_attendance.count_documents({'student_id': sid, 'date': {'$regex': f'^{month}'}, 'meal_type': 'dinner', 'present': True})
            result.append({'student': student, 'breakfast': breakfast_count, 'lunch': lunch_count, 'dinner': dinner_count, 'total': breakfast_count + lunch_count + dinner_count})
        return render_template('shared/mess_summary.html', summary=result, month=month)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/mess_summary.html', summary=[], month='')
