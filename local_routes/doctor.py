from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from local_models import Doctor, TimeSlot, Appointment
from local_db import db
from datetime import datetime, date, time

doctor_bp = Blueprint('doctor_bp', __name__)

def require_doctor():
    if 'user_id' not in session or session.get('user_role') != 'doctor':
        return redirect(url_for('auth_bp.login'))
    return None

def get_doctor_profile():
    user_id = session.get('user_id')
    return Doctor.query.filter_by(user_id=user_id).first()

@doctor_bp.route('/doctor')
def dashboard():
    redirect_response = require_doctor()
    if redirect_response:
        return redirect_response
    
    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth_bp.logout'))
    
    # Get today's appointments
    today = date.today()
    today_appointments = Appointment.query.join(TimeSlot).filter(
        Appointment.doctor_id == doctor.id,
        TimeSlot.date == today
    ).order_by(TimeSlot.start_time).all()
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.join(TimeSlot).filter(
        Appointment.doctor_id == doctor.id,
        TimeSlot.date > today,
        Appointment.status == 'scheduled'
    ).order_by(TimeSlot.date, TimeSlot.start_time).limit(10).all()
    
    # Get statistics
    total_appointments = Appointment.query.filter_by(doctor_id=doctor.id).count()
    pending_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id, 
        status='scheduled'
    ).count()
    
    return render_template('doctor/dashboard.html',
                         doctor=doctor,
                         today_appointments=today_appointments,
                         upcoming_appointments=upcoming_appointments,
                         total_appointments=total_appointments,
                         pending_appointments=pending_appointments)

@doctor_bp.route('/doctor/appointments')
def appointments():
    redirect_response = require_doctor()
    if redirect_response:
        return redirect_response
    
    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth_bp.logout'))
    
    # Get all appointments for this doctor
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(
        Appointment.created_at.desc()
    ).all()
    
    return render_template('doctor/appointments.html', 
                         doctor=doctor, 
                         appointments=appointments)

@doctor_bp.route('/doctor/schedule')
def schedule():
    redirect_response = require_doctor()
    if redirect_response:
        return redirect_response
    
    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth_bp.logout'))
    
    # Get all time slots for this doctor
    time_slots = TimeSlot.query.filter_by(doctor_id=doctor.id).order_by(
        TimeSlot.date, TimeSlot.start_time
    ).all()
    
    return render_template('doctor/schedule.html', 
                         doctor=doctor, 
                         time_slots=time_slots)

@doctor_bp.route('/doctor/schedule/add', methods=['GET', 'POST'])
def add_schedule():
    redirect_response = require_doctor()
    if redirect_response:
        return redirect_response
    
    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth_bp.logout'))
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        
        if not all([date_str, start_time, end_time]):
            flash('All fields are required.', 'error')
            return render_template('doctor/add_schedule.html', doctor=doctor)
        
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Check if time slot already exists
            existing_slot = TimeSlot.query.filter_by(
                doctor_id=doctor.id,
                date=appointment_date,
                start_time=start_time,
                end_time=end_time
            ).first()
            
            if existing_slot:
                flash('A time slot already exists for this date and time.', 'warning')
                return render_template('doctor/add_schedule.html', doctor=doctor)
            
            time_slot = TimeSlot(
                doctor_id=doctor.id,
                date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                is_available=True
            )
            
            db.session.add(time_slot)
            db.session.commit()
            flash('Time slot added successfully!', 'success')
            return redirect(url_for('doctor_bp.schedule'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the time slot.', 'error')
    
    return render_template('doctor/add_schedule.html', doctor=doctor)

@doctor_bp.route('/doctor/appointment/<int:appointment_id>/complete', methods=['POST'])
def complete_appointment(appointment_id):
    redirect_response = require_doctor()
    if redirect_response:
        return redirect_response
    
    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth_bp.logout'))
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first_or_404()
    
    appointment.status = 'completed'
    
    try:
        db.session.commit()
        flash('Appointment marked as completed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the appointment.', 'error')
    
    return redirect(url_for('doctor_bp.appointments'))

@doctor_bp.route('/doctor/time-slot/<int:slot_id>/toggle', methods=['POST'])
def toggle_availability(slot_id):
    redirect_response = require_doctor()
    if redirect_response:
        return redirect_response
    
    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth_bp.logout'))
    
    time_slot = TimeSlot.query.filter_by(
        id=slot_id,
        doctor_id=doctor.id
    ).first_or_404()
    
    time_slot.is_available = not time_slot.is_available
    
    try:
        db.session.commit()
        status = 'available' if time_slot.is_available else 'unavailable'
        flash(f'Time slot marked as {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the time slot.', 'error')
    
    return redirect(url_for('doctor_bp.schedule'))