from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required
from datetime import datetime
from ..db import get_db
from ..utils import role_required, safe_object_id
import csv
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
@role_required('admin', 'warden')
def index():
    return render_template('shared/reports.html')

@reports_bp.route('/occupancy')
@login_required
@role_required('admin', 'warden')
def occupancy():
    try:
        db = get_db()
        result = []
        for block in db.blocks.find():
            for room in db.rooms.find({'block_id': str(block['_id'])}):
                occupied = db.allocations.count_documents({'room_id': str(room['_id']), 'status': 'Active'})
                students_in_room = []
                for alloc in db.allocations.find({'room_id': str(room['_id']), 'status': 'Active'}):
                    student = db.students.find_one({'_id': safe_object_id(alloc.get('student_id', ''))})
                    if student:
                        students_in_room.append(student['name'])
                result.append({
                    'block': block['name'], 'room_number': room['room_number'],
                    'room_type': room.get('room_type', ''), 'capacity': room.get('capacity', 0),
                    'occupied': occupied, 'vacant': room.get('capacity', 0) - occupied,
                    'status': room.get('status', ''), 'students': ', '.join(students_in_room)
                })
        return render_template('shared/report_occupancy.html', data=result)
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('reports.index'))

@reports_bp.route('/occupancy/csv')
@login_required
@role_required('admin', 'warden')
def occupancy_csv():
    db = get_db()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Block', 'Room', 'Type', 'Capacity', 'Occupied', 'Vacant', 'Status', 'Students'])
    for block in db.blocks.find():
        for room in db.rooms.find({'block_id': str(block['_id'])}):
            occupied = db.allocations.count_documents({'room_id': str(room['_id']), 'status': 'Active'})
            students_in_room = []
            for alloc in db.allocations.find({'room_id': str(room['_id']), 'status': 'Active'}):
                student = db.students.find_one({'_id': safe_object_id(alloc.get('student_id', ''))})
                if student:
                    students_in_room.append(student['name'])
            writer.writerow([block['name'], room['room_number'], room.get('room_type',''), room.get('capacity',0), occupied, room.get('capacity',0)-occupied, room.get('status',''), ', '.join(students_in_room)])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=occupancy_report.csv'})

@reports_bp.route('/fees')
@login_required
@role_required('admin', 'warden')
def fee_report():
    try:
        db = get_db()
        result = []
        for student in db.students.find({'status': 'Active'}):
            sid = str(student['_id'])
            fees = list(db.fees.find({'student_id': sid}))
            total_amount = sum(f.get('amount', 0) for f in fees)
            paid_amount = sum(f.get('paid_amount', 0) for f in fees)
            pending = total_amount - paid_amount
            result.append({
                'student_name': student['name'], 'roll_number': student.get('roll_number', ''),
                'total_amount': total_amount, 'paid_amount': paid_amount, 'pending': pending,
                'status': 'Paid' if pending == 0 and total_amount > 0 else ('Partial' if paid_amount > 0 else 'Pending')
            })
        return render_template('shared/report_fees.html', data=result)
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('reports.index'))

@reports_bp.route('/fees/csv')
@login_required
@role_required('admin', 'warden')
def fee_report_csv():
    db = get_db()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Roll Number', 'Total Amount', 'Paid Amount', 'Pending', 'Status'])
    for student in db.students.find({'status': 'Active'}):
        sid = str(student['_id'])
        fees = list(db.fees.find({'student_id': sid}))
        total_amount = sum(f.get('amount', 0) for f in fees)
        paid_amount = sum(f.get('paid_amount', 0) for f in fees)
        pending = total_amount - paid_amount
        status = 'Paid' if pending == 0 and total_amount > 0 else ('Partial' if paid_amount > 0 else 'Pending')
        writer.writerow([student['name'], student.get('roll_number', ''), total_amount, paid_amount, pending, status])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=fee_report.csv'})

@reports_bp.route('/defaulters')
@login_required
@role_required('admin', 'warden')
def defaulters():
    try:
        db = get_db()
        result = []
        for fee in db.fees.find({'status': {'$in': ['Pending', 'Partial']}}):
            student = db.students.find_one({'_id': safe_object_id(fee.get('student_id', ''))})
            if student:
                result.append({
                    'student_name': student['name'], 'roll_number': student.get('roll_number', ''),
                    'phone': student.get('phone', ''), 'fee_type': fee.get('fee_type', ''),
                    'amount': fee.get('amount', 0), 'paid': fee.get('paid_amount', 0),
                    'pending': fee.get('amount', 0) - fee.get('paid_amount', 0),
                    'due_date': fee.get('due_date', ''), 'status': fee.get('status', '')
                })
        return render_template('shared/report_defaulters.html', defaulters=result)
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('reports.index'))

@reports_bp.route('/defaulters/csv')
@login_required
@role_required('admin', 'warden')
def defaulters_csv():
    db = get_db()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Roll Number', 'Phone', 'Fee Type', 'Total', 'Paid', 'Pending', 'Due Date', 'Status'])
    for fee in db.fees.find({'status': {'$in': ['Pending', 'Partial']}}):
        student = db.students.find_one({'_id': safe_object_id(fee.get('student_id', ''))})
        if student:
            writer.writerow([student['name'], student.get('roll_number',''), student.get('phone',''), fee.get('fee_type',''), fee.get('amount',0), fee.get('paid_amount',0), fee.get('amount',0)-fee.get('paid_amount',0), fee.get('due_date',''), fee.get('status','')])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=defaulters_report.csv'})
