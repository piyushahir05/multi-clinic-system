from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Doctor
from app import db
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
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.role != role:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Invalid role for this user'}), 401
                flash('Invalid role for this user', 'error')
                return render_template('login.html')
            
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
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Validate input
        required_fields = ['email', 'password', 'full_name', 'username']
        for field in required_fields:
            if not data.get(field):
                message = f'{field.replace("_", " ").title()} is required'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 400
                flash(message, 'error')
                return render_template('register.html')
        
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        full_name = data.get('full_name')
        phone = data.get('phone')
        age = data.get('age')
        gender = data.get('gender')
        blood_group = data.get('blood_group')
        
        # Validate email and password
        if not validate_email(email):
            message = 'Invalid email format'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'error')
            return render_template('register.html')
        
        if not validate_password(password):
            message = 'Password must be at least 6 characters long'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            message = 'Email already registered'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            message = 'Username already taken'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            phone=phone,
            age=int(age) if age else None,
            gender=gender,
            blood_group=blood_group,
            role='patient'
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Auto login after registration
            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.full_name
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Registration successful',
                    'redirect': url_for('dashboard')
                })
            
            flash('Registration successful! Welcome!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            message = 'Registration failed. Please try again.'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 500
            flash(message, 'error')
    
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('home'))

@auth_bp.route('/check-session')
def check_session():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user_id': session['user_id'],
            'user_role': session['user_role'],
            'user_name': session['user_name']
        })
    return jsonify({'authenticated': False})
