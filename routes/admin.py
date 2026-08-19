from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from datetime import datetime
from database.db import query_db, execute_db
from routes.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Dynamic Statistics directly from DB
    stats = {
        'total_slots': query_db("SELECT COUNT(*) as c FROM parking_slots", one=True)['c'],
        'available_slots': query_db("SELECT COUNT(*) as c FROM parking_slots WHERE status = 'available'", one=True)['c'],
        'occupied_slots': query_db("SELECT COUNT(*) as c FROM parking_slots WHERE status = 'occupied'", one=True)['c'],
        'maintenance_slots': query_db("SELECT COUNT(*) as c FROM parking_slots WHERE status = 'maintenance'", one=True)['c'],
        'total_users': query_db("SELECT COUNT(*) as c FROM users WHERE role = 'user'", one=True)['c'],
        'total_bookings': query_db("SELECT COUNT(*) as c FROM bookings", one=True)['c'],
        'active_bookings': query_db("SELECT COUNT(*) as c FROM bookings WHERE booking_status = 'active'", one=True)['c'],
        'completed_bookings': query_db("SELECT COUNT(*) as c FROM bookings WHERE booking_status = 'completed'", one=True)['c'],
    }

    # All slots for overview grid
    slots = query_db("SELECT * FROM parking_slots ORDER BY slot_number ASC")

    # Recent bookings (latest 6)
    recent_bookings = query_db("""
        SELECT b.*, u.name as user_name, u.email as user_email, 
               v.vehicle_number, v.vehicle_type, s.slot_number, s.section
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN vehicles v ON b.vehicle_id = v.id
        JOIN parking_slots s ON b.slot_id = s.id
        ORDER BY b.created_at DESC
        LIMIT 6
    """)

    return render_template('admin/dashboard.html', stats=stats, slots=slots, recent_bookings=recent_bookings)

@admin_bp.route('/slots', methods=['GET'])
@admin_required
def slots():
    search = request.args.get('search', '').strip()
    section_filter = request.args.get('section', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = "SELECT * FROM parking_slots WHERE 1=1"
    params = []

    if search:
        query += " AND (slot_number LIKE %s OR section LIKE %s OR floor LIKE %s)"
        like_search = f"%{search}%"
        params.extend([like_search, like_search, like_search])
    if section_filter:
        query += " AND section = %s"
        params.append(section_filter)
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)

    query += " ORDER BY slot_number ASC"
    slots_list = query_db(query, tuple(params))

    sections = [row['section'] for row in query_db("SELECT DISTINCT section FROM parking_slots ORDER BY section")]

    return render_template(
        'admin/slots.html',
        slots=slots_list,
        sections=sections,
        search=search,
        selected_section=section_filter,
        selected_status=status_filter
    )

@admin_bp.route('/slots/add', methods=['POST'])
@admin_required
def add_slot():
    slot_number = request.form.get('slot_number', '').strip().upper()
    section = request.form.get('section', '').strip()
    floor = request.form.get('floor', '').strip()
    vehicle_type = request.form.get('vehicle_type', 'Car').strip()
    status = request.form.get('status', 'available').strip()

    if not slot_number or not section or not floor:
        flash('Slot number, section, and floor are mandatory fields.', 'danger')
        return redirect(url_for('admin.slots'))

    # Check duplicate slot number
    existing = query_db("SELECT id FROM parking_slots WHERE slot_number = %s", (slot_number,), one=True)
    if existing:
        flash(f'Slot number "{slot_number}" already exists in the system.', 'warning')
        return redirect(url_for('admin.slots'))

    execute_db(
        "INSERT INTO parking_slots (slot_number, section, floor, vehicle_type, status) VALUES (%s, %s, %s, %s, %s)",
        (slot_number, section, floor, vehicle_type, status)
    )
    flash(f'Parking slot "{slot_number}" created successfully!', 'success')
    return redirect(url_for('admin.slots'))

@admin_bp.route('/slots/edit/<int:slot_id>', methods=['POST'])
@admin_required
def edit_slot(slot_id):
    slot = query_db("SELECT * FROM parking_slots WHERE id = %s", (slot_id,), one=True)
    if not slot:
        flash('Slot not found.', 'danger')
        return redirect(url_for('admin.slots'))

    slot_number = request.form.get('slot_number', '').strip().upper()
    section = request.form.get('section', '').strip()
    floor = request.form.get('floor', '').strip()
    vehicle_type = request.form.get('vehicle_type', 'Car').strip()
    status = request.form.get('status', 'available').strip()

    # Check unique constraint if changing slot number
    if slot_number != slot['slot_number']:
        existing = query_db("SELECT id FROM parking_slots WHERE slot_number = %s AND id != %s", (slot_number, slot_id), one=True)
        if existing:
            flash(f'Another slot with number "{slot_number}" already exists.', 'warning')
            return redirect(url_for('admin.slots'))

    execute_db("""
        UPDATE parking_slots 
        SET slot_number = %s, section = %s, floor = %s, vehicle_type = %s, status = %s 
        WHERE id = %s
    """, (slot_number, section, floor, vehicle_type, status, slot_id))

    flash(f'Slot "{slot_number}" details updated successfully.', 'success')
    return redirect(url_for('admin.slots'))

@admin_bp.route('/slots/delete/<int:slot_id>', methods=['POST'])
@admin_required
def delete_slot(slot_id):
    slot = query_db("SELECT * FROM parking_slots WHERE id = %s", (slot_id,), one=True)
    if not slot:
        flash('Slot not found.', 'danger')
        return redirect(url_for('admin.slots'))

    # Check if there are active bookings
    active_booking = query_db(
        "SELECT id FROM bookings WHERE slot_id = %s AND booking_status IN ('active', 'booked')",
        (slot_id,),
        one=True
    )
    if active_booking:
        flash(f'Cannot delete Slot "{slot["slot_number"]}" because there are scheduled or active bookings associated with it. Update or cancel those bookings first.', 'danger')
        return redirect(url_for('admin.slots'))

    execute_db("DELETE FROM parking_slots WHERE id = %s", (slot_id,))
    flash(f'Slot "{slot["slot_number"]}" deleted permanently.', 'info')
    return redirect(url_for('admin.slots'))

@admin_bp.route('/users')
@admin_required
def users():
    search = request.args.get('search', '').strip()

    query = """
        SELECT u.id, u.name, u.email, u.phone, u.role, u.created_at,
               COUNT(DISTINCT v.id) as vehicle_count,
               COUNT(DISTINCT b.id) as booking_count
        FROM users u
        LEFT JOIN vehicles v ON u.id = v.user_id
        LEFT JOIN bookings b ON u.id = b.user_id
        WHERE u.role = 'user'
    """
    params = []

    if search:
        query += " AND (u.name LIKE %s OR u.email LIKE %s OR u.phone LIKE %s)"
        like_str = f"%{search}%"
        params.extend([like_str, like_str, like_str])

    query += " GROUP BY u.id, u.name, u.email, u.phone, u.role, u.created_at ORDER BY u.created_at DESC"
    users_list = query_db(query, tuple(params))

    return render_template('admin/users.html', users=users_list, search=search)

@admin_bp.route('/bookings')
@admin_required
def bookings():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    date_filter = request.args.get('date', '').strip()

    query = """
        SELECT b.*, u.name as user_name, u.email as user_email,
               v.vehicle_number, v.vehicle_type,
               s.slot_number, s.section, s.floor
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN vehicles v ON b.vehicle_id = v.id
        JOIN parking_slots s ON b.slot_id = s.id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (u.name LIKE %s OR u.email LIKE %s OR v.vehicle_number LIKE %s OR s.slot_number LIKE %s)"
        like_str = f"%{search}%"
        params.extend([like_str, like_str, like_str, like_str])
    if status_filter:
        query += " AND b.booking_status = %s"
        params.append(status_filter)
    if date_filter:
        query += " AND b.booking_date = %s"
        params.append(date_filter)

    query += " ORDER BY b.created_at DESC"
    bookings_list = query_db(query, tuple(params))

    return render_template(
        'admin/bookings.html',
        bookings=bookings_list,
        search=search,
        selected_status=status_filter,
        selected_date=date_filter
    )

@admin_bp.route('/bookings/<int:booking_id>/status', methods=['POST'])
@admin_required
def update_booking_status(booking_id):
    new_status = request.form.get('status', '').strip().lower()
    if new_status not in ['booked', 'active', 'completed', 'cancelled']:
        flash('Invalid booking status provided.', 'danger')
        return redirect(url_for('admin.bookings'))

    booking = query_db("SELECT * FROM bookings WHERE id = %s", (booking_id,), one=True)
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('admin.bookings'))

    # Update booking
    execute_db("UPDATE bookings SET booking_status = %s WHERE id = %s", (new_status, booking_id))

    # Update slot and history records according to transition
    if new_status == 'active':
        execute_db("UPDATE parking_slots SET status = 'occupied' WHERE id = %s", (booking['slot_id'],))
        # Ensure parking_history reflects Active state and entry_time
        existing_hist = query_db("SELECT id FROM parking_history WHERE booking_id = %s", (booking_id,), one=True)
        if existing_hist:
            execute_db("UPDATE parking_history SET status = 'Active', entry_time = IFNULL(entry_time, NOW()) WHERE booking_id = %s", (booking_id,))
        else:
            v_num = query_db("SELECT vehicle_number FROM vehicles WHERE id = %s", (booking['vehicle_id'],), one=True)['vehicle_number']
            s_num = query_db("SELECT slot_number FROM parking_slots WHERE id = %s", (booking['slot_id'],), one=True)['slot_number']
            execute_db("INSERT INTO parking_history (booking_id, vehicle_number, slot_number, entry_time, status) VALUES (%s, %s, %s, NOW(), 'Active')", (booking_id, v_num, s_num))

    elif new_status == 'completed':
        execute_db("UPDATE parking_slots SET status = 'available' WHERE id = %s AND status = 'occupied'", (booking['slot_id'],))
        execute_db("UPDATE parking_history SET status = 'Completed', exit_time = IFNULL(exit_time, NOW()) WHERE booking_id = %s", (booking_id,))

    elif new_status == 'cancelled':
        execute_db("UPDATE parking_slots SET status = 'available' WHERE id = %s AND status = 'occupied'", (booking['slot_id'],))
        execute_db("UPDATE parking_history SET status = 'Cancelled', exit_time = NOW() WHERE booking_id = %s", (booking_id,))

    elif new_status == 'booked':
        execute_db("UPDATE parking_slots SET status = 'available' WHERE id = %s AND status = 'occupied'", (booking['slot_id'],))
        execute_db("UPDATE parking_history SET status = 'Booked' WHERE booking_id = %s", (booking_id,))

    flash(f"Booking #{booking_id} status changed to '{new_status.capitalize()}'.", 'success')
    return redirect(url_for('admin.bookings'))

@admin_bp.route('/history')
@admin_required
def history():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    sort_order = request.args.get('sort', 'DESC').upper()
    if sort_order not in ['ASC', 'DESC']:
        sort_order = 'DESC'

    query = """
        SELECT h.*, b.booking_date, u.name as user_name, u.email as user_email
        FROM parking_history h
        LEFT JOIN bookings b ON h.booking_id = b.id
        LEFT JOIN users u ON b.user_id = u.id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (h.vehicle_number LIKE %s OR h.slot_number LIKE %s OR u.name LIKE %s)"
        like_str = f"%{search}%"
        params.extend([like_str, like_str, like_str])
    if status_filter:
        query += " AND h.status = %s"
        params.append(status_filter)

    query += f" ORDER BY h.created_at {sort_order}"
    records = query_db(query, tuple(params))

    return render_template(
        'admin/history.html',
        history=records,
        search=search,
        selected_status=status_filter,
        sort_order=sort_order
    )
