from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from ..db import get_db
from ..utils import role_required, safe_object_id

visitors_bp = Blueprint('visitors', __name__, url_prefix='/visitors')

@visitors_bp.route('/')
@login_required
@role_required('admin', 'warden')
def index():
    try:
        db = get_db()
        search = request.args.get('search', '')
        date_filter = request.args.get('date', '')
        page = int(request.args.get('page', 1))
        per_page = 10
        query = {}
        if date_filter:
            query['visit_date'] = date_filter
        visitors = list(db.visitors.find(query).sort('in_time', -1))
        result = []
        for v in visitors:
            if search and search.lower() not in (v.get('visitor_name', '') + v.get('student_visited', '')).lower():
                continue
            result.append(v)
        total = len(result)
        total_pages = max(1, (total + per_page - 1) // per_page)
        paginated = result[(page-1)*per_page:page*per_page]
        return render_template('shared/visitors_list.html', visitors=paginated, search=search, date_filter=date_filter, page=page, total_pages=total_pages, total=total)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/visitors_list.html', visitors=[], search='', date_filter='', page=1, total_pages=1, total=0)

@visitors_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'warden')
def add():
    db = get_db()
    students = list(db.students.find({'status': 'Active'}))
    if request.method == 'POST':
        try:
            visitor_name = request.form.get('visitor_name', '').strip()
            student_id = request.form.get('student_id', '').strip()
            purpose = request.form.get('purpose', '').strip()
            in_time = request.form.get('in_time', '').strip()
            visit_date = request.form.get('visit_date', date.today().isoformat())
            if not all([visitor_name, student_id, purpose, in_time]):
                flash('All required fields must be filled.', 'danger')
                return render_template('shared/visitor_form.html', students=students, visitor=None)
            student = db.students.find_one({'_id': safe_object_id(student_id)})
            db.visitors.insert_one({
                'visitor_name': visitor_name, 'student_id': student_id,
                'student_visited': student['name'] if student else 'Unknown',
                'purpose': purpose, 'in_time': in_time, 'out_time': '',
                'visit_date': visit_date, 'created_at': datetime.now()
            })
            flash('Visitor entry recorded.', 'success')
            return redirect(url_for('visitors.index'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('shared/visitor_form.html', students=students, visitor=None)

@visitors_bp.route('/update-out/<visitor_id>', methods=['POST'])
@login_required
@role_required('admin', 'warden')
def update_out(visitor_id):
    db = get_db()
    oid = safe_object_id(visitor_id)
    if oid:
        out_time = request.form.get('out_time', datetime.now().strftime('%H:%M'))
        db.visitors.update_one({'_id': oid}, {'$set': {'out_time': out_time}})
        flash('Out time updated.', 'success')
    return redirect(url_for('visitors.index'))
