from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from models import User, Clinic, Doctor, TimeSlot, Appointment
from app import db
from datetime import datetime, date, time
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin_bp', __name__)

def require_admin():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('auth_bp.login'))
    return None

@admin_bp.route('/dashboard')
def dashboard():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    # Get summary statistics
    stats = {
        'total_patients': User.query.filter_by(role='patient').count(),
        'total_doctors': Doctor.query.count(),
        'total_clinics': Clinic.query.count(),
        'total_appointments': Appointment.query.count(),
        'pending_appointments': Appointment.query.filter_by(status='scheduled').count()
    }
    
    # Get recent appointments
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', stats=stats, recent_appointments=recent_appointments)

# Clinic Management
@admin_bp.route('/clinics')
def manage_clinics():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    clinics = Clinic.query.all()
    return render_template('admin_dashboard.html', section='clinics', clinics=clinics)

@admin_bp.route('/api/clinics', methods=['GET', 'POST'])
def api_clinics():
    auth_check = require_admin()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        data = request.get_json()
        
        required_fields = ['name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        clinic = Clinic(
            name=data['name'],
            address=data.get('address', ''),
            phone=data.get('phone', ''),
            description=data.get('description', '')
        )
        
        try:
            db.session.add(clinic)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Clinic added successfully', 'clinic': clinic.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Failed to add clinic'}), 500
    
    # GET request
    clinics = Clinic.query.all()
    return jsonify([clinic.to_dict() for clinic in clinics])

@admin_bp.route('/api/clinics/<int:clinic_id>', methods=['PUT', 'DELETE'])
def api_clinic_detail(clinic_id):
    auth_check = require_admin()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    clinic = Clinic.query.get_or_404(clinic_id)
    
    if request.method == 'PUT':
        data = request.get_json()
        
        clinic.name = data.get('name', clinic.name)
        clinic.address = data.get('address', clinic.address)
        clinic.phone = data.get('phone', clinic.phone)
        clinic.description = data.get('description', clinic.description)
        
        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Clinic updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Failed to update clinic'}), 500
    
    if request.method == 'DELETE':
        try:
            # Check if clinic has doctors
            if clinic.doctors:
                return jsonify({'success': False, 'message': 'Cannot delete clinic with assigned doctors'}), 400
            
            db.session.delete(clinic)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Clinic deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Failed to delete clinic'}), 500

# Doctor Management
@admin_bp.route('/doctors')
def manage_doctors():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    doctors = Doctor.query.all()
    clinics = Clinic.query.all()
    return render_template('admin_dashboard.html', section='doctors', doctors=doctors, clinics=clinics)

@admin_bp.route('/api/doctors', methods=['GET', 'POST'])
def api_doctors():
    auth_check = require_admin()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        data = request.get_json()
        
        required_fields = ['email', 'password', 'full_name', 'username', 'clinic_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'message': 'Username already taken'}), 400
        
        try:
            # Create user account for doctor
            user = User(
                email=data['email'],
                username=data['username'],
                full_name=data['full_name'],
                phone=data.get('phone', ''),
                role='doctor'
            )
            user.set_password(data['password'])
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create doctor profile
            doctor = Doctor(
                user_id=user.id,
                clinic_id=data['clinic_id'],
                specialization=data.get('specialization', ''),
                qualification=data.get('qualification', ''),
                experience_years=data.get('experience_years', 0),
                consultation_fee=data.get('consultation_fee', 0.0)
            )
            db.session.add(doctor)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Doctor added successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Failed to add doctor'}), 500
    
    # GET request
    doctors = Doctor.query.all()
    return jsonify([doctor.to_dict() for doctor in doctors])

@admin_bp.route('/api/doctors/<int:doctor_id>', methods=['PUT', 'DELETE'])
def api_doctor_detail(doctor_id):
    auth_check = require_admin()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'PUT':
        data = request.get_json()
        
        # Update doctor profile
        doctor.clinic_id = data.get('clinic_id', doctor.clinic_id)
        doctor.specialization = data.get('specialization', doctor.specialization)
        doctor.qualification = data.get('qualification', doctor.qualification)
        doctor.experience_years = data.get('experience_years', doctor.experience_years)
        doctor.consultation_fee = data.get('consultation_fee', doctor.consultation_fee)
        
        # Update user details
        if data.get('full_name'):
            doctor.user.full_name = data['full_name']
        if data.get('phone'):
            doctor.user.phone = data['phone']
        
        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Doctor updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Failed to update doctor'}), 500
    
    if request.method == 'DELETE':
        try:
            # Check if doctor has appointments
            if doctor.appointments:
                return jsonify({'success': False, 'message': 'Cannot delete doctor with existing appointments'}), 400
            
            # Delete time slots first
            TimeSlot.query.filter_by(doctor_id=doctor_id).delete()
            
            # Delete doctor profile
            user = doctor.user
            db.session.delete(doctor)
            db.session.delete(user)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Doctor deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Failed to delete doctor'}), 500

# Time Slot Management
@admin_bp.route('/slots')
def manage_slots():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    slots = TimeSlot.query.order_by(TimeSlot.date.desc(), TimeSlot.start_time.desc()).limit(50).all()
    doctors = Doctor.query.all()
    return render_template('admin_dashboard.html', section='slots', slots=slots, doctors=doctors)

@admin_bp.route('/api/slots', methods=['GET', 'POST'])
def api_slots():
    auth_check = require_admin()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        data = request.get_json()
        
        required_fields = ['doctor_id', 'date', 'start_time', 'end_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        try:
            slot_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            
            # Check for conflicting slots
            existing_slot = TimeSlot.query.filter(
                TimeSlot.doctor_id == data['doctor_id'],
                TimeSlot.date == slot_date,
                TimeSlot.start_time < end_time,
                TimeSlot.end_time > start_time
            ).first()
            
            if existing_slot:
                return jsonify({'success': False, 'message': 'Time slot conflicts with existing slot'}), 400
            
            slot = TimeSlot(
                doctor_id=data['doctor_id'],
                date=slot_date,
                start_time=start_time,
                end_time=end_time,
                is_available=True
            )
            
            db.session.add(slot)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Time slot added successfully'})
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid date or time format'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Failed to add time slot'}), 500
    
    # GET request
    doctor_id = request.args.get('doctor_id')
    query = TimeSlot.query
    
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
    
    slots = query.order_by(TimeSlot.date.desc(), TimeSlot.start_time.desc()).limit(100).all()
    return jsonify([slot.to_dict() for slot in slots])

@admin_bp.route('/api/slots/<int:slot_id>', methods=['DELETE'])
def api_slot_detail(slot_id):
    auth_check = require_admin()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    slot = TimeSlot.query.get_or_404(slot_id)
    
    try:
        # Check if slot has appointments
        if slot.appointments:
            return jsonify({'success': False, 'message': 'Cannot delete slot with existing appointments'}), 400
        
        db.session.delete(slot)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Time slot deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete time slot'}), 500

# Appointment Management
@admin_bp.route('/appointments')
def manage_appointments():
    auth_check = require_admin()
    if auth_check:
        return auth_check
    
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).all()
    return render_template('admin_dashboard.html', section='appointments', appointments=appointments)

@admin_bp.route('/api/appointments')
def api_appointments():
    auth_check = require_admin()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).all()
    return jsonify([appointment.to_dict() for appointment in appointments])
