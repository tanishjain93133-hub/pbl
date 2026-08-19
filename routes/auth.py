import functools
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import query_db, execute_db

auth_bp = Blueprint('auth', __name__)

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    """View decorator that restricts access strictly to admin users."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Admin authentication required.', 'warning')
            return redirect(url_for('auth.admin_login', next=request.url))
        if session.get('role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('user.dashboard'))
        return view(**kwargs)
    return wrapped_view

@auth_bp.before_app_request
def load_logged_in_user():
    """Load logged-in user into Flask's application context 'g' for templates."""
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = query_db("SELECT id, name, email, phone, role FROM users WHERE id = %s", (user_id,), one=True)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('admin.dashboard' if session.get('role') == 'admin' else 'user.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        errors = []
        if not name:
            errors.append("Full Name is required.")
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("A valid email address is required.")
        if not phone or len(phone) < 7 or not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            errors.append("A valid contact phone number is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        # Check email uniqueness
        if not errors:
            existing_user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
            if existing_user:
                errors.append("An account with this email address already exists. Please log in.")

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', name=name, email=email, phone=phone)

        # Hash password and store
        pwd_hash = generate_password_hash(password)
        execute_db(
            "INSERT INTO users (name, email, phone, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
            (name, email, phone, pwd_hash, 'user')
        )

        flash('Registration successful! You can now log in to SmartPark.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('admin.dashboard' if session.get('role') == 'admin' else 'user.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'warning')
            return render_template('login.html', email=email)

        user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = user['role']

            flash(f"Welcome back, {user['name']}!", 'success')
            next_page = request.args.get('next')
            if next_page and not next_page.startswith('/admin'):
                return redirect(next_page)
            return redirect(url_for('admin.dashboard' if user['role'] == 'admin' else 'user.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session and session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter admin credentials.', 'warning')
            return render_template('admin/login.html', email=email)

        user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)

        if user and check_password_hash(user['password_hash'], password):
            if user['role'] != 'admin':
                flash('Access denied. This account does not have administrator privileges.', 'danger')
                return render_template('admin/login.html', email=email)

            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = 'admin'

            flash('Admin authentication successful. Welcome to Admin Control Panel.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid administrator credentials.', 'danger')
            return render_template('admin/login.html', email=email)

    return render_template('admin/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been safely logged out.', 'info')
    return redirect(url_for('auth.login'))
