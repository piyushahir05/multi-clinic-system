from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from local_models import User, Doctor
from local_db import db
from utils.validation import validate_email, validate_password

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            role = data.get('role', 'patient')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'patient')
        
        if not email or not password:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Email and password are required'}), 400
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.role != role:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Invalid role for this user'}), 401
                flash('Invalid role for this user', 'error')
                return render_template('auth/login.html')
            
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.full_name
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'redirect': url_for('dashboard')
                })
            
            return redirect(url_for('dashboard'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        role = data.get('role', 'patient')
        
        # Validation
        errors = []
        
        if not name or len(name.strip()) < 2:
            errors.append('Name must be at least 2 characters long')
        
        if not email:
            errors.append('Email is required')
        elif not validate_email(email):
            errors.append('Please enter a valid email address')
        
        if not phone or len(phone.strip()) < 10:
            errors.append('Please enter a valid phone number')
        
        if not password:
            errors.append('Password is required')
        elif not validate_password(password):
            errors.append('Password must be at least 8 characters long and contain uppercase, lowercase, and number')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if role not in ['patient', 'doctor', 'admin']:
            errors.append('Invalid role selected')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            errors.append('An account with this email already exists')
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        new_user = User(
            name=name.strip(),
            email=email.lower().strip(),
            phone=phone.strip(),
            role=role
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Account created successfully',
                    'redirect': url_for('auth_bp.login')
                })
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth_bp.login'))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'message': 'An error occurred while creating your account'}), 500
            flash('An error occurred while creating your account. Please try again.', 'error')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    
    user_role = session.get('user_role')
    
    if user_role == 'admin':
        return redirect(url_for('admin_bp.dashboard'))
    elif user_role == 'doctor':
        return redirect(url_for('doctor_bp.dashboard'))
    elif user_role == 'patient':
        return redirect(url_for('booking_bp.my_appointments'))
    else:
        flash('Invalid user role', 'error')
        return redirect(url_for('auth_bp.login'))