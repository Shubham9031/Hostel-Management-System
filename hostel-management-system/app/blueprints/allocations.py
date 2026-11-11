from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from datetime import datetime
from ..db import get_db
from ..utils import role_required, safe_object_id
from bson import ObjectId

allocations_bp = Blueprint('allocations', __name__, url_prefix='/allocations')

@allocations_bp.route('/')
@login_required
@role_required('admin', 'warden')
def index():
    try:
        db = get_db()
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = 10
        allocations = list(db.allocations.find({'status': 'Active'}).sort('allocated_at', -1))
        result = []
        for alloc in allocations:
            student = db.students.find_one({'_id': safe_object_id(alloc.get('student_id', ''))})
            room = db.rooms.find_one({'_id': safe_object_id(alloc.get('room_id', ''))})
            block = None
            if room:
                block = db.blocks.find_one({'_id': safe_object_id(room.get('block_id', ''))})
            if search:
                if student and search.lower() not in (student.get('name','') + student.get('roll_number','')).lower():
                    continue
            alloc['student_name'] = student['name'] if student else 'Unknown'
            alloc['student_roll'] = student['roll_number'] if student else ''
            alloc['room_number'] = room['room_number'] if room else 'Unknown'
            alloc['block_name'] = block['name'] if block else 'Unknown'
            result.append(alloc)
        total = len(result)
        total_pages = max(1, (total + per_page - 1) // per_page)
        paginated = result[(page-1)*per_page:page*per_page]
        return render_template('shared/allocations_list.html', allocations=paginated, search=search, page=page, total_pages=total_pages, total=total)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/allocations_list.html', allocations=[], search='', page=1, total_pages=1, total=0)

@allocations_bp.route('/assign', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def assign():
    db = get_db()
    allocated_student_ids = [a['student_id'] for a in db.allocations.find({'status': 'Active'}, {'student_id': 1})]
    unallocated_students = list(db.students.find({'status': 'Active', '_id': {'$nin': [safe_object_id(sid) for sid in allocated_student_ids if sid]}}))
    available_rooms = []
    for room in db.rooms.find({'status': {'$ne': 'Maintenance'}}):
        occupied = db.allocations.count_documents({'room_id': str(room['_id']), 'status': 'Active'})
        if occupied < room.get('capacity', 1):
            block = db.blocks.find_one({'_id': safe_object_id(room.get('block_id', ''))})
            room['block_name'] = block['name'] if block else 'Unknown'
            room['available_beds'] = room.get('capacity', 1) - occupied
            available_rooms.append(room)
    if request.method == 'POST':
        try:
            student_id = request.form.get('student_id', '').strip()
            room_id = request.form.get('room_id', '').strip()
            if not all([student_id, room_id]):
                flash('Student and room are required.', 'danger')
                return render_template('shared/allocation_form.html', students=unallocated_students, rooms=available_rooms)
            if db.allocations.find_one({'student_id': student_id, 'status': 'Active'}):
                flash('Student already has an active room allocation.', 'danger')
                return render_template('shared/allocation_form.html', students=unallocated_students, rooms=available_rooms)
            room = db.rooms.find_one({'_id': safe_object_id(room_id)})
            if not room:
                flash('Room not found.', 'danger')
                return render_template('shared/allocation_form.html', students=unallocated_students, rooms=available_rooms)
            occupied = db.allocations.count_documents({'room_id': room_id, 'status': 'Active'})
            if occupied >= room.get('capacity', 1):
                flash('Room is at full capacity.', 'danger')
                return render_template('shared/allocation_form.html', students=unallocated_students, rooms=available_rooms)
            db.allocations.insert_one({
                'student_id': student_id, 'room_id': room_id,
                'allocated_at': datetime.now(), 'status': 'Active',
                'notes': request.form.get('notes', '').strip()
            })
            new_occupied = occupied + 1
            if new_occupied >= room.get('capacity', 1):
                db.rooms.update_one({'_id': safe_object_id(room_id)}, {'$set': {'status': 'Full'}})
            flash('Room allocated successfully.', 'success')
            return redirect(url_for('allocations.index'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('shared/allocation_form.html', students=unallocated_students, rooms=available_rooms)

@allocations_bp.route('/checkout/<allocation_id>', methods=['POST'])
@login_required
@role_required('admin', 'warden')
def checkout(allocation_id):
    db = get_db()
    oid = safe_object_id(allocation_id)
    if not oid:
        flash('Invalid allocation ID.', 'danger')
        return redirect(url_for('allocations.index'))
    alloc = db.allocations.find_one({'_id': oid})
    if alloc:
        db.allocations.update_one({'_id': oid}, {'$set': {'status': 'Checked-out', 'checked_out_at': datetime.now()}})
        db.rooms.update_one({'_id': safe_object_id(alloc['room_id'])}, {'$set': {'status': 'Available'}})
        student = db.students.find_one({'_id': safe_object_id(alloc['student_id'])})
        if student:
            db.students.update_one({'_id': safe_object_id(alloc['student_id'])}, {'$set': {'status': 'Checked-out'}})
        flash('Student checked out successfully.', 'success')
    return redirect(url_for('allocations.index'))

@allocations_bp.route('/history')
@login_required
@role_required('admin', 'warden')
def history():
    try:
        db = get_db()
        page = int(request.args.get('page', 1))
        per_page = 10
        all_allocs = list(db.allocations.find().sort('allocated_at', -1))
        result = []
        for alloc in all_allocs:
            student = db.students.find_one({'_id': safe_object_id(alloc.get('student_id', ''))})
            room = db.rooms.find_one({'_id': safe_object_id(alloc.get('room_id', ''))})
            block = None
            if room:
                block = db.blocks.find_one({'_id': safe_object_id(room.get('block_id', ''))})
            alloc['student_name'] = student['name'] if student else 'Unknown'
            alloc['room_number'] = room['room_number'] if room else 'Unknown'
            alloc['block_name'] = block['name'] if block else 'Unknown'
            result.append(alloc)
        total = len(result)
        total_pages = max(1, (total + per_page - 1) // per_page)
        paginated = result[(page-1)*per_page:page*per_page]
        return render_template('shared/allocation_history.html', allocations=paginated, page=page, total_pages=total_pages, total=total)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/allocation_history.html', allocations=[], page=1, total_pages=1, total=0)
