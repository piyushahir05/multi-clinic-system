from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from models import Clinic, Doctor, TimeSlot, Appointment, User
from app import db
from datetime import datetime, date

booking_bp = Blueprint('booking_bp', __name__)

def require_patient():
    if 'user_id' not in session or session.get('user_role') != 'patient':
        return redirect(url_for('auth_bp.login'))
    return None

@booking_bp.route('/clinics')
def select_clinic():
    auth_check = require_patient()
    if auth_check:
        return auth_check
    
    clinics = Clinic.query.all()
    return render_template('booking.html', step='clinic', clinics=clinics)

@booking_bp.route('/api/clinics')
def api_get_clinics():
    clinics = Clinic.query.all()
    return jsonify([clinic.to_dict() for clinic in clinics])

@booking_bp.route('/doctors/<int:clinic_id>')
def select_doctor(clinic_id):
    auth_check = require_patient()
    if auth_check:
        return auth_check
    
    clinic = Clinic.query.get_or_404(clinic_id)
    doctors = Doctor.query.filter_by(clinic_id=clinic_id).all()
    
    return render_template('booking.html', step='doctor', clinic=clinic, doctors=doctors)

@booking_bp.route('/api/doctors/<int:clinic_id>')
def api_get_doctors(clinic_id):
    doctors = Doctor.query.filter_by(clinic_id=clinic_id).all()
    return jsonify([doctor.to_dict() for doctor in doctors])

@booking_bp.route('/slots/<int:doctor_id>')
def select_slot(doctor_id):
    auth_check = require_patient()
    if auth_check:
        return auth_check
    
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Get available time slots for the next 30 days
    today = date.today()
    available_slots = TimeSlot.query.filter(
        TimeSlot.doctor_id == doctor_id,
        TimeSlot.date >= today,
        TimeSlot.is_available == True
    ).order_by(TimeSlot.date, TimeSlot.start_time).all()
    
    return render_template('booking.html', step='slot', doctor=doctor, slots=available_slots)

@booking_bp.route('/api/slots/<int:doctor_id>')
def api_get_slots(doctor_id):
    today = date.today()
    available_slots = TimeSlot.query.filter(
        TimeSlot.doctor_id == doctor_id,
        TimeSlot.date >= today,
        TimeSlot.is_available == True
    ).order_by(TimeSlot.date, TimeSlot.start_time).all()
    
    return jsonify([slot.to_dict() for slot in available_slots])

@booking_bp.route('/confirm/<int:slot_id>', methods=['GET', 'POST'])
def confirm_booking(slot_id):
    auth_check = require_patient()
    if auth_check:
        return auth_check
    
    slot = TimeSlot.query.get_or_404(slot_id)
    
    if not slot.is_available:
        flash('This time slot is no longer available', 'error')
        return redirect(url_for('booking_bp.select_slot', doctor_id=slot.doctor_id))
    
    if request.method == 'POST':
        try:
            # Double-check slot availability before booking
            slot = TimeSlot.query.filter_by(id=slot_id, is_available=True).first()
            if not slot:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Slot no longer available'}), 400
                flash('This time slot is no longer available', 'error')
                return redirect(url_for('booking_bp.select_slot', doctor_id=slot.doctor_id))
            
            # Create appointment
            appointment = Appointment(
                patient_id=session['user_id'],
                doctor_id=slot.doctor_id,
                time_slot_id=slot_id,
                status='scheduled'
            )
            
            # Mark slot as unavailable
            slot.is_available = False
            
            db.session.add(appointment)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Appointment booked successfully',
                    'appointment_id': appointment.id
                })
            
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('booking_bp.booking_success', appointment_id=appointment.id))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'message': 'Booking failed. Please try again.'}), 500
            flash('Booking failed. Please try again.', 'error')
            return redirect(url_for('booking_bp.select_slot', doctor_id=slot.doctor_id))
    
    return render_template('booking.html', step='confirm', slot=slot)

@booking_bp.route('/success/<int:appointment_id>')
def booking_success(appointment_id):
    auth_check = require_patient()
    if auth_check:
        return auth_check
    
    appointment = Appointment.query.filter_by(
        id=appointment_id, 
        patient_id=session['user_id']
    ).first_or_404()
    
    return render_template('appointment_success.html', appointment=appointment)

@booking_bp.route('/my-appointments')
def my_appointments():
    auth_check = require_patient()
    if auth_check:
        return auth_check
    
    appointments = Appointment.query.filter_by(patient_id=session['user_id']).order_by(Appointment.created_at.desc()).all()
    return render_template('booking.html', step='appointments', appointments=appointments)

@booking_bp.route('/api/my-appointments')
def api_my_appointments():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    appointments = Appointment.query.filter_by(patient_id=session['user_id']).order_by(Appointment.created_at.desc()).all()
    return jsonify([appointment.to_dict() for appointment in appointments])
