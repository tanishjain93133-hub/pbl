from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from database.db import query_db, execute_db
from routes.auth import login_required
from werkzeug.security import generate_password_hash, check_password_hash
import re

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    
    # 1. Total available slots
    available_slots_count = query_db("SELECT COUNT(*) as count FROM parking_slots WHERE status = 'available'", one=True)['count']
    
    # 2. User total bookings
    total_bookings_count = query_db("SELECT COUNT(*) as count FROM bookings WHERE user_id = %s", (user_id,), one=True)['count']
    
    # 3. User total registered vehicles
    total_vehicles_count = query_db("SELECT COUNT(*) as count FROM vehicles WHERE user_id = %s", (user_id,), one=True)['count']
    
    # 4. Active or Upcoming Booking
    active_booking = query_db("""
        SELECT b.*, s.slot_number, s.section, s.floor, v.vehicle_number, v.vehicle_type, v.vehicle_model
        FROM bookings b
        JOIN parking_slots s ON b.slot_id = s.id
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.user_id = %s AND b.booking_status IN ('active', 'booked')
        ORDER BY b.booking_date ASC, b.start_time ASC
        LIMIT 1
    """, (user_id,), one=True)
    
    # 5. Recent bookings snippet (last 3)
    recent_bookings = query_db("""
        SELECT b.*, s.slot_number, s.section, v.vehicle_number
        FROM bookings b
        JOIN parking_slots s ON b.slot_id = s.id
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.user_id = %s
        ORDER BY b.created_at DESC
        LIMIT 4
    """, (user_id,))
    
    # 6. User vehicles list for quick modal booking or dashboard display
    user_vehicles = query_db("SELECT * FROM vehicles WHERE user_id = %s ORDER BY created_at DESC", (user_id,))

    return render_template(
        'dashboard.html',
        available_slots_count=available_slots_count,
        total_bookings_count=total_bookings_count,
        total_vehicles_count=total_vehicles_count,
        active_booking=active_booking,
        recent_bookings=recent_bookings,
        user_vehicles=user_vehicles
    )

@user_bp.route('/vehicles', methods=['GET'])
@login_required
def vehicles():
    user_id = session['user_id']
    user_vehicles = query_db("SELECT * FROM vehicles WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    return render_template('vehicles.html', vehicles=user_vehicles)

@user_bp.route('/vehicles/add', methods=['POST'])
@login_required
def add_vehicle():
    user_id = session['user_id']
    vehicle_number = request.form.get('vehicle_number', '').strip().upper().replace(' ', '')
    vehicle_type = request.form.get('vehicle_type', 'Car').strip()
    vehicle_model = request.form.get('vehicle_model', '').strip()

    if not vehicle_number:
        flash('Vehicle registration number is required.', 'danger')
        return redirect(url_for('user.vehicles'))

    if len(vehicle_number) < 5 or len(vehicle_number) > 20:
        flash('Please enter a valid vehicle registration number (e.g., GJ01AB1234).', 'danger')
        return redirect(url_for('user.vehicles'))

    # Check if duplicate vehicle for this user
    existing = query_db("SELECT id FROM vehicles WHERE user_id = %s AND vehicle_number = %s", (user_id, vehicle_number), one=True)
    if existing:
        flash(f'Vehicle {vehicle_number} is already registered under your account.', 'warning')
        return redirect(url_for('user.vehicles'))

    execute_db(
        "INSERT INTO vehicles (user_id, vehicle_number, vehicle_type, vehicle_model) VALUES (%s, %s, %s, %s)",
        (user_id, vehicle_number, vehicle_type, vehicle_model or 'Standard')
    )
    flash(f'Vehicle {vehicle_number} added successfully!', 'success')
    return redirect(url_for('user.vehicles'))

@user_bp.route('/vehicles/edit/<int:vehicle_id>', methods=['POST'])
@login_required
def edit_vehicle(vehicle_id):
    user_id = session['user_id']
    vehicle = query_db("SELECT * FROM vehicles WHERE id = %s AND user_id = %s", (vehicle_id, user_id), one=True)
    if not vehicle:
        flash('Vehicle not found or unauthorized access.', 'danger')
        return redirect(url_for('user.vehicles'))

    vehicle_number = request.form.get('vehicle_number', '').strip().upper().replace(' ', '')
    vehicle_type = request.form.get('vehicle_type', 'Car').strip()
    vehicle_model = request.form.get('vehicle_model', '').strip()

    if not vehicle_number or len(vehicle_number) < 5:
        flash('Please provide a valid vehicle registration number.', 'danger')
        return redirect(url_for('user.vehicles'))

    execute_db(
        "UPDATE vehicles SET vehicle_number = %s, vehicle_type = %s, vehicle_model = %s WHERE id = %s AND user_id = %s",
        (vehicle_number, vehicle_type, vehicle_model or 'Standard', vehicle_id, user_id)
    )
    flash(f'Vehicle {vehicle_number} updated successfully.', 'success')
    return redirect(url_for('user.vehicles'))

@user_bp.route('/vehicles/delete/<int:vehicle_id>', methods=['POST'])
@login_required
def delete_vehicle(vehicle_id):
    user_id = session['user_id']
    vehicle = query_db("SELECT * FROM vehicles WHERE id = %s AND user_id = %s", (vehicle_id, user_id), one=True)
    if not vehicle:
        flash('Vehicle not found or unauthorized access.', 'danger')
        return redirect(url_for('user.vehicles'))

    # Check for active bookings
    active_booking = query_db(
        "SELECT id FROM bookings WHERE vehicle_id = %s AND booking_status IN ('active', 'booked')",
        (vehicle_id,),
        one=True
    )
    if active_booking:
        flash('Cannot delete vehicle because it is currently linked to an active or scheduled booking. Cancel the booking first.', 'danger')
        return redirect(url_for('user.vehicles'))

    execute_db("DELETE FROM vehicles WHERE id = %s AND user_id = %s", (vehicle_id, user_id))
    flash(f"Vehicle {vehicle['vehicle_number']} has been removed.", 'info')
    return redirect(url_for('user.vehicles'))

@user_bp.route('/history', methods=['GET'])
@login_required
def history():
    user_id = session['user_id']
    
    # Filter parameters
    vehicle_filter = request.args.get('vehicle', '').strip()
    status_filter = request.args.get('status', '').strip()
    sort_order = request.args.get('sort', 'DESC').upper()
    if sort_order not in ['ASC', 'DESC']:
        sort_order = 'DESC'

    # Get user's vehicles for filter dropdown
    user_vehicles = query_db("SELECT * FROM vehicles WHERE user_id = %s", (user_id,))
    user_vehicle_numbers = [v['vehicle_number'] for v in user_vehicles]

    if not user_vehicle_numbers:
        return render_template('history.html', history=[], user_vehicles=[], selected_vehicle='', selected_status='', sort_order=sort_order)

    # Build query
    query = """
        SELECT h.*
        FROM parking_history h
        WHERE h.vehicle_number IN ({})
    """.format(','.join(['%s'] * len(user_vehicle_numbers)))
    params = list(user_vehicle_numbers)

    if vehicle_filter:
        query += " AND h.vehicle_number = %s"
        params.append(vehicle_filter)
    if status_filter:
        query += " AND h.status = %s"
        params.append(status_filter)

    query += f" ORDER BY h.created_at {sort_order}"
    history_records = query_db(query, tuple(params))

    return render_template(
        'history.html',
        history=history_records,
        user_vehicles=user_vehicles,
        selected_vehicle=vehicle_filter,
        selected_status=status_filter,
        sort_order=sort_order
    )

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            if not name or not phone:
                flash('Name and Phone are required.', 'danger')
            else:
                execute_db("UPDATE users SET name = %s, phone = %s WHERE id = %s", (name, phone, user_id))
                session['user_name'] = name
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('user.profile'))
                
        elif action == 'change_password':
            current_pwd = request.form.get('current_password', '')
            new_pwd = request.form.get('new_password', '')
            confirm_pwd = request.form.get('confirm_new_password', '')

            if not check_password_hash(user['password_hash'], current_pwd):
                flash('Current password is incorrect.', 'danger')
            elif len(new_pwd) < 6:
                flash('New password must be at least 6 characters.', 'danger')
            elif new_pwd != confirm_pwd:
                flash('New passwords do not match.', 'danger')
            else:
                new_hash = generate_password_hash(new_pwd)
                execute_db("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
                flash('Password changed successfully!', 'success')
                return redirect(url_for('user.profile'))

    # Statistics for profile
    stats = {
        'total_bookings': query_db("SELECT COUNT(*) as c FROM bookings WHERE user_id = %s", (user_id,), one=True)['c'],
        'total_vehicles': query_db("SELECT COUNT(*) as c FROM vehicles WHERE user_id = %s", (user_id,), one=True)['c']
    }

    return render_template('profile.html', user=user, stats=stats)
