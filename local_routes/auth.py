from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from local_models import db, User, Patient
from local_db import db
from utils.validation import validate_email, validate_password

auth_bp = Blueprint('auth_bp', __name__)



@auth_bp.route('/about')
def about():
    return render_template('about.html', title="About Us")

@auth_bp.route('/contact')
def contact():
    return render_template('contact.html', title="Contact Us")


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
                    'redirect': url_for('auth_bp.dashboard')
                })
            
            return redirect(url_for('auth_bp.dashboard'))
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

        # Extract fields
        email = data.get('email')
        username = data.get('username')
        full_name = data.get('full_name')
        phone = data.get('phone')
        password = data.get('password')
        age = data.get('age')
        gender = data.get('gender')
        blood_group = data.get('blood_group')

        errors = []

        # Validations
        if not full_name or len(full_name.strip()) < 2:
            errors.append('Full name must be at least 2 characters long')

        if not username or len(username.strip()) < 3:
            errors.append('Username must be at least 3 characters long')

        if not email:
            errors.append('Email is required')
        elif not validate_email(email):
            errors.append('Invalid email address')

        if not password or not validate_password(password):
            errors.append('Password must be at least 8 characters with uppercase, lowercase, and number')

        if not phone or len(phone.strip()) < 10:
            errors.append('Phone number must be at least 10 digits')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            errors.append('An account with this email already exists')

        if errors:
            if request.is_json:
                return jsonify({'success': False, 'message': '; '.join(errors)}), 400
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')

        # Create User
        new_user = User(
            name=full_name.strip(),
            email=email.lower().strip(),
            phone=phone.strip(),
            username=username.strip(),
            role='patient'
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.flush()  # So we can access new_user.id before committing

            # Create Patient linked to this User
            new_patient = Patient(
                age=age,
                gender=gender,
                blood_group=blood_group,
                user_id=new_user.id
            )
            db.session.add(new_patient)
            db.session.commit()

            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('auth_bp.login')}), 200

            flash('Account created successfully!', 'success')
            return redirect(url_for('auth_bp.login'))

        except Exception as e:
            db.session.rollback()
            print("Error creating user or patient:", e)
            if request.is_json:
                return jsonify({'success': False, 'message': 'Server error'}), 500
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