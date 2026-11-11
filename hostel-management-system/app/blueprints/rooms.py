from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from datetime import datetime
from ..db import get_db
from ..utils import role_required, safe_object_id
from bson import ObjectId

rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')

@rooms_bp.route('/blocks')
@login_required
@role_required('admin', 'warden')
def blocks():
    try:
        db = get_db()
        all_blocks = list(db.blocks.find())
        for b in all_blocks:
            b['room_count'] = db.rooms.count_documents({'block_id': str(b['_id'])})
        return render_template('shared/blocks_list.html', blocks=all_blocks)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/blocks_list.html', blocks=[])

@rooms_bp.route('/blocks/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_block():
    if request.method == 'POST':
        try:
            db = get_db()
            name = request.form.get('name', '').strip()
            floors = request.form.get('floors', '1').strip()
            description = request.form.get('description', '').strip()
            if not name:
                flash('Block name is required.', 'danger')
                return render_template('shared/block_form.html', block=None, action='Add')
            if db.blocks.find_one({'name': name}):
                flash('Block with this name already exists.', 'danger')
                return render_template('shared/block_form.html', block=None, action='Add')
            db.blocks.insert_one({'name': name, 'floors': int(floors), 'description': description, 'created_at': datetime.now()})
            flash(f'Block {name} added successfully.', 'success')
            return redirect(url_for('rooms.blocks'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('shared/block_form.html', block=None, action='Add')

@rooms_bp.route('/blocks/edit/<block_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_block(block_id):
    db = get_db()
    oid = safe_object_id(block_id)
    if not oid:
        flash('Invalid block ID.', 'danger')
        return redirect(url_for('rooms.blocks'))
    block = db.blocks.find_one({'_id': oid})
    if not block:
        flash('Block not found.', 'danger')
        return redirect(url_for('rooms.blocks'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        floors = request.form.get('floors', '1').strip()
        description = request.form.get('description', '').strip()
        if not name:
            flash('Block name is required.', 'danger')
            return render_template('shared/block_form.html', block=block, action='Edit')
        db.blocks.update_one({'_id': oid}, {'$set': {'name': name, 'floors': int(floors), 'description': description}})
        flash('Block updated successfully.', 'success')
        return redirect(url_for('rooms.blocks'))
    return render_template('shared/block_form.html', block=block, action='Edit')

@rooms_bp.route('/blocks/delete/<block_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_block(block_id):
    db = get_db()
    oid = safe_object_id(block_id)
    if oid:
        if db.rooms.count_documents({'block_id': block_id}) > 0:
            flash('Cannot delete block with existing rooms.', 'danger')
        else:
            db.blocks.delete_one({'_id': oid})
            flash('Block deleted.', 'success')
    return redirect(url_for('rooms.blocks'))

@rooms_bp.route('/')
@login_required
@role_required('admin', 'warden')
def index():
    try:
        db = get_db()
        search = request.args.get('search', '')
        block_filter = request.args.get('block', '')
        page = int(request.args.get('page', 1))
        per_page = 10
        query = {}
        if search:
            query['room_number'] = {'$regex': search, '$options': 'i'}
        if block_filter:
            query['block_id'] = block_filter
        total = db.rooms.count_documents(query)
        rooms = list(db.rooms.find(query).skip((page-1)*per_page).limit(per_page))
        all_blocks = list(db.blocks.find())
        blocks_map = {str(b['_id']): b['name'] for b in all_blocks}
        for r in rooms:
            r['block_name'] = blocks_map.get(r.get('block_id', ''), 'Unknown')
            r['occupied'] = db.allocations.count_documents({'room_id': str(r['_id']), 'status': 'Active'})
        total_pages = (total + per_page - 1) // per_page
        return render_template('shared/rooms_list.html', rooms=rooms, all_blocks=all_blocks, search=search,
            block_filter=block_filter, page=page, total_pages=total_pages, total=total)
    except Exception as e:
        flash(str(e), 'danger')
        return render_template('shared/rooms_list.html', rooms=[], all_blocks=[], search='', block_filter='', page=1, total_pages=1, total=0)

@rooms_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add():
    db = get_db()
    all_blocks = list(db.blocks.find())
    if request.method == 'POST':
        try:
            block_id = request.form.get('block_id', '').strip()
            room_number = request.form.get('room_number', '').strip()
            floor = request.form.get('floor', '1').strip()
            room_type = request.form.get('room_type', 'Single')
            capacity = int(request.form.get('capacity', 1))
            status = request.form.get('status', 'Available')
            amenities = request.form.get('amenities', '').strip()
            if not all([block_id, room_number]):
                flash('Block and room number are required.', 'danger')
                return render_template('shared/room_form.html', room=None, all_blocks=all_blocks, action='Add')
            if db.rooms.find_one({'block_id': block_id, 'room_number': room_number}):
                flash('Room number already exists in this block.', 'danger')
                return render_template('shared/room_form.html', room=None, all_blocks=all_blocks, action='Add')
            db.rooms.insert_one({
                'block_id': block_id, 'room_number': room_number, 'floor': int(floor),
                'room_type': room_type, 'capacity': capacity, 'status': status,
                'amenities': amenities, 'created_at': datetime.now()
            })
            flash(f'Room {room_number} added successfully.', 'success')
            return redirect(url_for('rooms.index'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('shared/room_form.html', room=None, all_blocks=all_blocks, action='Add')

@rooms_bp.route('/edit/<room_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(room_id):
    db = get_db()
    oid = safe_object_id(room_id)
    if not oid:
        flash('Invalid room ID.', 'danger')
        return redirect(url_for('rooms.index'))
    room = db.rooms.find_one({'_id': oid})
    if not room:
        flash('Room not found.', 'danger')
        return redirect(url_for('rooms.index'))
    all_blocks = list(db.blocks.find())
    if request.method == 'POST':
        update_data = {
            'floor': int(request.form.get('floor', 1)),
            'room_type': request.form.get('room_type', 'Single'),
            'capacity': int(request.form.get('capacity', 1)),
            'status': request.form.get('status', 'Available'),
            'amenities': request.form.get('amenities', '').strip()
        }
        db.rooms.update_one({'_id': oid}, {'$set': update_data})
        flash('Room updated successfully.', 'success')
        return redirect(url_for('rooms.index'))
    return render_template('shared/room_form.html', room=room, all_blocks=all_blocks, action='Edit')

@rooms_bp.route('/delete/<room_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete(room_id):
    db = get_db()
    oid = safe_object_id(room_id)
    if oid:
        if db.allocations.count_documents({'room_id': room_id, 'status': 'Active'}) > 0:
            flash('Cannot delete room with active allocations.', 'danger')
        else:
            db.rooms.delete_one({'_id': oid})
            flash('Room deleted.', 'success')
    return redirect(url_for('rooms.index'))
