from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from datetime import datetime, date, time
from database.db import query_db, execute_db
from routes.auth import login_required

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/parking', methods=['GET'])
def parking():
    """Parking availability page displaying slot cards, filters, and legend."""
    section_filter = request.args.get('section', '').strip()
    floor_filter = request.args.get('floor', '').strip()
    vehicle_type_filter = request.args.get('vehicle_type', '').strip()
    status_filter = request.args.get('status', '').strip()

    # Base query for slots
    query = "SELECT * FROM parking_slots WHERE 1=1"
    params = []

    if section_filter:
        query += " AND section = %s"
        params.append(section_filter)
    if floor_filter:
        query += " AND floor = %s"
        params.append(floor_filter)
    if vehicle_type_filter:
        query += " AND vehicle_type = %s"
        params.append(vehicle_type_filter)
    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)

    query += " ORDER BY slot_number ASC"
    slots = query_db(query, tuple(params))

    # Distinct values for filter dropdowns
    sections = [row['section'] for row in query_db("SELECT DISTINCT section FROM parking_slots ORDER BY section")]
    floors = [row['floor'] for row in query_db("SELECT DISTINCT floor FROM parking_slots ORDER BY floor")]
    vehicle_types = [row['vehicle_type'] for row in query_db("SELECT DISTINCT vehicle_type FROM parking_slots ORDER BY vehicle_type")]

    # Statistics for parking availability banner
    stats = {
        'total': query_db("SELECT COUNT(*) as c FROM parking_slots", one=True)['c'],
        'available': query_db("SELECT COUNT(*) as c FROM parking_slots WHERE status = 'available'", one=True)['c'],
        'occupied': query_db("SELECT COUNT(*) as c FROM parking_slots WHERE status = 'occupied'", one=True)['c'],
        'maintenance': query_db("SELECT COUNT(*) as c FROM parking_slots WHERE status = 'maintenance'", one=True)['c']
    }

    # Load logged-in user's vehicles for the booking modal if authenticated
    user_vehicles = []
    if 'user_id' in session:
        user_vehicles = query_db("SELECT * FROM vehicles WHERE user_id = %s ORDER BY created_at DESC", (session['user_id'],))

    return render_template(
        'parking.html',
        slots=slots,
        sections=sections,
        floors=floors,
        vehicle_types=vehicle_types,
        stats=stats,
        selected_section=section_filter,
        selected_floor=floor_filter,
        selected_type=vehicle_type_filter,
        selected_status=status_filter,
        user_vehicles=user_vehicles,
        today=date.today().isoformat()
    )

@booking_bp.route('/booking/create', methods=['GET', 'POST'])
@login_required
def create_booking():
    user_id = session['user_id']
    user_vehicles = query_db("SELECT * FROM vehicles WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    
    if request.method == 'GET':
        slot_id = request.args.get('slot_id')
        selected_slot = None
        if slot_id:
            selected_slot = query_db("SELECT * FROM parking_slots WHERE id = %s", (slot_id,), one=True)
        
        available_slots = query_db("SELECT * FROM parking_slots WHERE status != 'maintenance' ORDER BY slot_number ASC")
        return render_template('booking.html', 
                               selected_slot=selected_slot, 
                               available_slots=available_slots, 
                               user_vehicles=user_vehicles, 
                               today=date.today().isoformat())

    # POST booking submission
    slot_id = request.form.get('slot_id')
    vehicle_id = request.form.get('vehicle_id')
    booking_date_str = request.form.get('booking_date', '').strip()
    start_time_str = request.form.get('start_time', '').strip()
    end_time_str = request.form.get('end_time', '').strip()

    # 1. Basic validation
    if not slot_id or not vehicle_id or not booking_date_str or not start_time_str or not end_time_str:
        flash('All booking fields are required.', 'danger')
        return redirect(url_for('booking.parking'))

    # 2. Verify Vehicle ownership
    vehicle = query_db("SELECT * FROM vehicles WHERE id = %s AND user_id = %s", (vehicle_id, user_id), one=True)
    if not vehicle:
        flash('Invalid vehicle selected or ownership mismatch.', 'danger')
        return redirect(url_for('booking.parking'))

    # 3. Verify Slot exists and is not in maintenance
    slot = query_db("SELECT * FROM parking_slots WHERE id = %s", (slot_id,), one=True)
    if not slot:
        flash('Selected parking slot does not exist.', 'danger')
        return redirect(url_for('booking.parking'))
    if slot['status'] == 'maintenance':
        flash('This parking slot is currently under maintenance and cannot be booked.', 'danger')
        return redirect(url_for('booking.parking'))

    # 4. Parse & Validate Dates and Times
    try:
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        today = date.today()
        if booking_date < today:
            flash('Booking date cannot be in the past.', 'danger')
            return redirect(url_for('booking.parking'))

        start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()

        if start_time_obj >= end_time_obj:
            flash('Booking end time must be strictly after start time.', 'danger')
            return redirect(url_for('booking.parking'))
    except ValueError:
        flash('Invalid date or time format.', 'danger')
        return redirect(url_for('booking.parking'))

    # 5. Overlapping Booking Conflict Check
    # Overlap occurs if existing_start < new_end AND existing_end > new_start
    conflict = query_db("""
        SELECT b.id, b.start_time, b.end_time 
        FROM bookings b
        WHERE b.slot_id = %s 
          AND b.booking_date = %s 
          AND b.booking_status IN ('booked', 'active')
          AND b.start_time < %s 
          AND b.end_time > %s
    """, (slot_id, booking_date_str, end_time_str + ':00', start_time_str + ':00'), one=True)

    if conflict:
        flash(f"Slot {slot['slot_number']} is already booked on {booking_date_str} during the requested hours ({conflict['start_time']} to {conflict['end_time']}). Please select another slot or time.", 'danger')
        return redirect(url_for('booking.parking'))

    # Determine initial booking status: if date is today and now is within the window, 'active', else 'booked'
    now = datetime.now()
    now_time = now.time()
    initial_status = 'booked'
    if booking_date == today and start_time_obj <= now_time < end_time_obj:
        initial_status = 'active'

    # 6. Insert Booking
    booking_id = execute_db("""
        INSERT INTO bookings (user_id, vehicle_id, slot_id, booking_date, start_time, end_time, booking_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (user_id, vehicle_id, slot_id, booking_date_str, start_time_str, end_time_str, initial_status))

    # 7. Update Slot status if active
    if initial_status == 'active':
        execute_db("UPDATE parking_slots SET status = 'occupied' WHERE id = %s", (slot_id,))
        # Insert initial entry into parking history
        execute_db("""
            INSERT INTO parking_history (booking_id, vehicle_number, slot_number, entry_time, status)
            VALUES (%s, %s, %s, NOW(), 'Active')
        """, (booking_id, vehicle['vehicle_number'], slot['slot_number']))
    else:
        # Scheduled for future
        execute_db("""
            INSERT INTO parking_history (booking_id, vehicle_number, slot_number, entry_time, status)
            VALUES (%s, %s, %s, NULL, 'Booked')
        """, (booking_id, vehicle['vehicle_number'], slot['slot_number']))

    flash(f"Parking slot {slot['slot_number']} booked successfully!", 'success')
    return redirect(url_for('booking.confirmation', booking_id=booking_id))

@booking_bp.route('/booking/confirmation/<int:booking_id>')
@login_required
def confirmation(booking_id):
    user_id = session['user_id']
    booking = query_db("""
        SELECT b.*, s.slot_number, s.section, s.floor, s.vehicle_type as slot_vehicle_type,
               v.vehicle_number, v.vehicle_type, v.vehicle_model, u.name as user_name, u.email as user_email
        FROM bookings b
        JOIN parking_slots s ON b.slot_id = s.id
        JOIN vehicles v ON b.vehicle_id = v.id
        JOIN users u ON b.user_id = u.id
        WHERE b.id = %s AND (b.user_id = %s OR %s = 'admin')
    """, (booking_id, user_id, session.get('role')), one=True)

    if not booking:
        flash('Booking record not found or access unauthorized.', 'danger')
        return redirect(url_for('user.dashboard'))

    return render_template('booking_confirm.html', booking=booking)

@booking_bp.route('/my-bookings')
@booking_bp.route('/bookings')
@login_required
def my_bookings():
    user_id = session['user_id']
    status_filter = request.args.get('status', '').strip()

    query = """
        SELECT b.*, s.slot_number, s.section, s.floor, v.vehicle_number, v.vehicle_type, v.vehicle_model
        FROM bookings b
        JOIN parking_slots s ON b.slot_id = s.id
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.user_id = %s
    """
    params = [user_id]

    if status_filter:
        query += " AND b.booking_status = %s"
        params.append(status_filter)

    query += " ORDER BY b.created_at DESC"
    bookings = query_db(query, tuple(params))

    return render_template('my_bookings.html', bookings=bookings, selected_status=status_filter)

@booking_bp.route('/booking/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    user_id = session['user_id']
    booking = query_db("SELECT * FROM bookings WHERE id = %s AND user_id = %s", (booking_id, user_id), one=True)

    if not booking:
        flash('Booking not found or unauthorized.', 'danger')
        return redirect(url_for('booking.my_bookings'))

    if booking['booking_status'] in ['completed', 'cancelled']:
        flash('This booking is already marked as completed or cancelled.', 'warning')
        return redirect(url_for('booking.my_bookings'))

    # Update booking status to cancelled
    execute_db("UPDATE bookings SET booking_status = 'cancelled' WHERE id = %s", (booking_id,))

    # If slot was occupied by this booking, restore slot to available
    execute_db("UPDATE parking_slots SET status = 'available' WHERE id = %s AND status = 'occupied'", (booking['slot_id'],))

    # Update parking history
    slot = query_db("SELECT slot_number FROM parking_slots WHERE id = %s", (booking['slot_id'],), one=True)
    vehicle = query_db("SELECT vehicle_number FROM vehicles WHERE id = %s", (booking['vehicle_id'],), one=True)
    
    execute_db("""
        UPDATE parking_history 
        SET status = 'Cancelled', exit_time = NOW() 
        WHERE booking_id = %s
    """, (booking_id,))

    flash(f"Booking #{booking_id} has been cancelled successfully.", 'info')
    return redirect(url_for('booking.my_bookings'))
