from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from ..db import get_db
from ..utils import role_required, safe_object_id
from bson import ObjectId

fees_bp = Blueprint('fees', __name__, url_prefix='/fees')

@fees_bp.route('/')
@login_required
@role_required('admin', 'warden')
def index():
    try:
        db = get_db()
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = 10
        fee_query = {}
        if status_filter:
            fee_query['status'] = status_filter
        fees = list(db.fees.find(fee_query).sort('created_at', -1))
        result = []
        for fee in fees:
            student = db.students.find_one({'_id': safe_object_id(fee.get('student_id', ''))})
            if search and student:
                if search.lower() not in (student.get('name','') + student.get('roll_number','')).lower():
                    continue
            fee['student_name'] = student['name'] if student else 'Unknown'
            fee['student_roll'] = student.get('roll_number', '') if student else ''
            result.append(fee)
        total = len(result)
        total_pages = max(1, (total + per_page - 1) // per_page)
        paginated = result[(page-1)*per_page:page*per_page]
        return render_template('shared/fees_list.html', fees=paginated, search=search, status_filter=status_filter, page=page, total_pages=total_pages, total=total)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/fees_list.html', fees=[], search='', status_filter='', page=1, total_pages=1, total=0)

@fees_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def add():
    db = get_db()
    students = list(db.students.find({'status': 'Active'}))
    if request.method == 'POST':
        try:
            student_id = request.form.get('student_id', '').strip()
            fee_type = request.form.get('fee_type', '').strip()
            amount = float(request.form.get('amount', 0))
            due_date = request.form.get('due_date', '').strip()
            description = request.form.get('description', '').strip()
            if not all([student_id, fee_type, amount, due_date]):
                flash('All required fields must be filled.', 'danger')
                return render_template('shared/fee_form.html', students=students, fee=None, action='Add')
            db.fees.insert_one({
                'student_id': student_id, 'fee_type': fee_type, 'amount': amount,
                'paid_amount': 0, 'due_date': due_date, 'description': description,
                'status': 'Pending', 'created_at': datetime.now()
            })
            flash('Fee record added successfully.', 'success')
            return redirect(url_for('fees.index'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('shared/fee_form.html', students=students, fee=None, action='Add')

@fees_bp.route('/pay/<fee_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def pay(fee_id):
    db = get_db()
    oid = safe_object_id(fee_id)
    if not oid:
        flash('Invalid fee ID.', 'danger')
        return redirect(url_for('fees.index'))
    fee = db.fees.find_one({'_id': oid})
    if not fee:
        flash('Fee record not found.', 'danger')
        return redirect(url_for('fees.index'))
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
            payment_date = request.form.get('payment_date', datetime.now().strftime('%Y-%m-%d'))
            mode = request.form.get('mode', 'Cash')
            receipt_number = request.form.get('receipt_number', '').strip()
            if amount <= 0:
                flash('Payment amount must be positive.', 'danger')
                return render_template('shared/payment_form.html', fee=fee)
            remaining = fee.get('amount', 0) - fee.get('paid_amount', 0)
            if amount > remaining:
                flash(f'Payment amount cannot exceed remaining balance of {remaining:.2f}.', 'danger')
                return render_template('shared/payment_form.html', fee=fee, now=datetime.now())
            db.payments.insert_one({
                'fee_id': fee_id, 'student_id': fee.get('student_id', ''),
                'amount': amount, 'payment_date': payment_date,
                'mode': mode, 'receipt_number': receipt_number,
                'recorded_by': current_user.id, 'created_at': datetime.now()
            })
            new_paid = fee.get('paid_amount', 0) + amount
            new_status = 'Paid' if new_paid >= fee.get('amount', 0) else 'Partial'
            db.fees.update_one({'_id': oid}, {'$set': {'paid_amount': new_paid, 'status': new_status}})
            flash(f'Payment of {amount:.2f} recorded successfully.', 'success')
            return redirect(url_for('fees.receipt', payment_id=str(db.payments.find_one({'fee_id': fee_id, 'amount': amount}, sort=[('created_at', -1)])['_id'])))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('shared/payment_form.html', fee=fee, now=datetime.now())

@fees_bp.route('/receipt/<payment_id>')
@login_required
def receipt(payment_id):
    db = get_db()
    oid = safe_object_id(payment_id)
    if not oid:
        flash('Invalid payment ID.', 'danger')
        return redirect(url_for('fees.index'))
    payment = db.payments.find_one({'_id': oid})
    if not payment:
        flash('Payment not found.', 'danger')
        return redirect(url_for('fees.index'))
    fee = db.fees.find_one({'_id': safe_object_id(payment.get('fee_id', ''))})
    student = db.students.find_one({'_id': safe_object_id(fee.get('student_id', ''))}) if fee else None
    return render_template('shared/receipt.html', payment=payment, fee=fee, student=student)

@fees_bp.route('/defaulters')
@login_required
@role_required('admin', 'warden')
def defaulters():
    try:
        db = get_db()
        defaulter_fees = list(db.fees.find({'status': {'$in': ['Pending', 'Partial']}}))
        result = []
        for fee in defaulter_fees:
            student = db.students.find_one({'_id': safe_object_id(fee.get('student_id', ''))})
            if student:
                fee['student_name'] = student['name']
                fee['student_roll'] = student.get('roll_number', '')
                fee['overdue'] = fee.get('amount', 0) - fee.get('paid_amount', 0)
                result.append(fee)
        return render_template('shared/defaulters.html', defaulters=result)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/defaulters.html', defaulters=[])

@fees_bp.route('/my-fees')
@login_required
@role_required('student')
def my_fees():
    try:
        db = get_db()
        student = db.students.find_one({'user_id': current_user.id})
        if not student:
            flash('Student profile not found.', 'warning')
            return render_template('shared/my_fees.html', fees=[], payments=[])
        fees = list(db.fees.find({'student_id': str(student['_id'])}))
        fee_ids = [str(f['_id']) for f in fees]
        payments = list(db.payments.find({'fee_id': {'$in': fee_ids}}).sort('created_at', -1))
        for f in fees:
            f['payments'] = [p for p in payments if p.get('fee_id') == str(f['_id'])]
        return render_template('shared/my_fees.html', fees=fees, payments=payments)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/my_fees.html', fees=[], payments=[])
