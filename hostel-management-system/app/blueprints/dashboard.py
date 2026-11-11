from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..db import get_db
from ..utils import role_required
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    try:
        db = get_db()
        if current_user.role in ['admin', 'warden']:
            total_students = db.students.count_documents({'status': 'Active'})
            total_rooms = db.rooms.count_documents({})
            occupied_beds = db.allocations.count_documents({'status': 'Active'})
            total_capacity = sum(r.get('capacity', 0) for r in db.rooms.find({}, {'capacity': 1}))
            vacant_beds = max(0, total_capacity - occupied_beds)
            open_complaints = db.complaints.count_documents({'status': 'Open'})
            pending_leaves = db.leaves.count_documents({'status': 'Pending'})
            pending_fees_data = list(db.fees.find({'status': {'$in': ['Pending', 'Partial']}}))
            pending_fees_total = sum(f.get('amount', 0) - f.get('paid_amount', 0) for f in pending_fees_data)
            recent_notices = list(db.notices.find().sort('created_at', -1).limit(5))
            occupancy_data = []
            for block in db.blocks.find():
                block_rooms = list(db.rooms.find({'block_id': str(block['_id'])}))
                block_capacity = sum(r.get('capacity', 0) for r in block_rooms)
                room_ids = [str(r['_id']) for r in block_rooms]
                block_occupied = db.allocations.count_documents({'room_id': {'$in': room_ids}, 'status': 'Active'})
                occupancy_data.append({'block': block['name'], 'occupied': block_occupied, 'total': block_capacity})
            monthly_fees = []
            for i in range(6, 0, -1):
                from datetime import timedelta
                month_start = (datetime.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
                month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
                month_total = sum(p.get('amount', 0) for p in db.payments.find({'payment_date': {'$gte': month_start.strftime('%Y-%m-%d'), '$lt': month_end.strftime('%Y-%m-%d')}}))
                monthly_fees.append({'month': month_start.strftime('%b %Y'), 'amount': month_total})
            return render_template('shared/dashboard_admin.html',
                total_students=total_students, total_rooms=total_rooms,
                occupied_beds=occupied_beds, vacant_beds=vacant_beds,
                open_complaints=open_complaints, pending_leaves=pending_leaves,
                pending_fees_total=pending_fees_total, recent_notices=recent_notices,
                occupancy_data=occupancy_data, monthly_fees=monthly_fees)
        else:
            from bson import ObjectId
            student = db.students.find_one({'user_id': current_user.id})
            my_allocation = None
            my_room = None
            my_block = None
            if student:
                my_allocation = db.allocations.find_one({'student_id': str(student['_id']), 'status': 'Active'})
                if my_allocation:
                    my_room = db.rooms.find_one({'_id': ObjectId(my_allocation['room_id'])})
                    if my_room:
                        my_block = db.blocks.find_one({'_id': ObjectId(my_room['block_id'])})
            my_fees = list(db.fees.find({'student_id': str(student['_id']) if student else None}))
            my_complaints = list(db.complaints.find({'student_id': str(student['_id']) if student else None}).sort('created_at', -1).limit(3))
            my_leaves = list(db.leaves.find({'student_id': str(student['_id']) if student else None}).sort('created_at', -1).limit(3))
            notices = list(db.notices.find().sort('created_at', -1).limit(5))
            pending_fee = sum(f.get('amount', 0) - f.get('paid_amount', 0) for f in my_fees if f.get('status') in ['Pending', 'Partial'])
            return render_template('shared/dashboard_student.html',
                student=student, my_allocation=my_allocation,
                my_room=my_room, my_block=my_block,
                my_fees=my_fees, pending_fee=pending_fee,
                my_complaints=my_complaints, my_leaves=my_leaves,
                notices=notices)
    except ConnectionError as e:
        return render_template('shared/db_error.html', error=str(e))
    except Exception as e:
        return render_template('shared/db_error.html', error=str(e))
