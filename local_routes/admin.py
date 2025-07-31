from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from local_models import User, Clinic, Doctor, TimeSlot, Appointment
from local_db import db
from datetime import datetime, date, time
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin_bp', __name__)

def require_admin():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('auth_bp.login'))
    return None

@admin_bp.route('/admin')
def dashboard():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Get summary statistics
    total_patients = User.query.filter_by(role='patient').count()
    total_doctors = User.query.filter_by(role='doctor').count()
    total_clinics = Clinic.query.count()
    total_appointments = Appointment.query.count()
    
    # Recent appointments
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         total_patients=total_patients,
                         total_doctors=total_doctors,
                         total_clinics=total_clinics,
                         total_appointments=total_appointments,
                         recent_appointments=recent_appointments)

@admin_bp.route('/admin/clinics')
def manage_clinics():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    clinics = Clinic.query.all()
    return render_template('admin/manage_clinics.html', clinics=clinics)

@admin_bp.route('/admin/clinics/add', methods=['GET', 'POST'])
def add_clinic():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        if not name or not address:
            flash('Clinic name and address are required.', 'error')
            return render_template('admin/add_clinic.html')
        
        clinic = Clinic(
            name=name.strip(),
            address=address.strip(),
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None
        )
        
        try:
            db.session.add(clinic)
            db.session.commit()
            flash('Clinic added successfully!', 'success')
            return redirect(url_for('admin_bp.manage_clinics'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the clinic.', 'error')
    
    return render_template('admin/add_clinic.html')

@admin_bp.route('/admin/doctors')
def manage_doctors():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    doctors = Doctor.query.all()
    return render_template('admin/manage_doctors.html', doctors=doctors)

@admin_bp.route('/admin/doctors/add', methods=['GET', 'POST'])
def add_doctor():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    clinics = Clinic.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        clinic_id = request.form.get('clinic_id')
        specialization = request.form.get('specialization')
        license_number = request.form.get('license_number')
        years_experience = request.form.get('years_experience')
        
        if not all([name, email, password, clinic_id]):
            flash('Name, email, password, and clinic are required.', 'error')
            return render_template('admin/add_doctor.html', clinics=clinics)
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('A user with this email already exists.', 'error')
            return render_template('admin/add_doctor.html', clinics=clinics)
        
        # Create user account
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            phone=phone.strip() if phone else None,
            role='doctor'
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Create doctor profile
            doctor = Doctor(
                user_id=user.id,
                clinic_id=int(clinic_id),
                specialization=specialization.strip() if specialization else None,
                license_number=license_number.strip() if license_number else None,
                years_experience=int(years_experience) if years_experience else None
            )
            
            db.session.add(doctor)
            db.session.commit()
            flash('Doctor added successfully!', 'success')
            return redirect(url_for('admin_bp.manage_doctors'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the doctor.', 'error')
    
    return render_template('admin/add_doctor.html', clinics=clinics)

@admin_bp.route('/admin/appointments')
def manage_appointments():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).all()
    return render_template('admin/manage_appointments.html', appointments=appointments)

@admin_bp.route('/admin/time-slots')
def manage_time_slots():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    time_slots = TimeSlot.query.order_by(TimeSlot.date.desc(), TimeSlot.start_time).all()
    return render_template('admin/manage_time_slots.html', time_slots=time_slots)

@admin_bp.route('/admin/time-slots/add', methods=['GET', 'POST'])
def add_time_slot():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    doctors = Doctor.query.all()
    
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        date_str = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        
        if not all([doctor_id, date_str, start_time, end_time]):
            flash('All fields are required.', 'error')
            return render_template('admin/add_time_slot.html', doctors=doctors)
        
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            time_slot = TimeSlot(
                doctor_id=int(doctor_id),
                date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                is_available=True
            )
            
            db.session.add(time_slot)
            db.session.commit()
            flash('Time slot added successfully!', 'success')
            return redirect(url_for('admin_bp.manage_time_slots'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the time slot.', 'error')
    
    return render_template('admin/add_time_slot.html', doctors=doctors)