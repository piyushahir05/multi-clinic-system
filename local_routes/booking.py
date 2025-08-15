from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from local_models import Clinic, Doctor, TimeSlot, Appointment, User
from local_db import db
from datetime import datetime, date
from collections import defaultdict


booking_bp = Blueprint('booking_bp', __name__)

def require_patient():
    if 'user_id' not in session or session.get('user_role') != 'patient':
        return redirect(url_for('auth_bp.login'))
    return None

@booking_bp.route('/book-appointment')
def book_appointment():
    redirect_response = require_patient()
    if redirect_response:
        return redirect_response
    
    return redirect(url_for('booking_bp.select_clinic'))

@booking_bp.route('/book/select-clinic')
def select_clinic():
    redirect_response = require_patient()
    if redirect_response:
        return redirect_response
    
    clinics = Clinic.query.all()
    return render_template('booking/select_clinic.html', clinics=clinics)

@booking_bp.route('/book/select-doctor/<int:clinic_id>')
def select_doctor(clinic_id):
    redirect_response = require_patient()
    if redirect_response:
        return redirect_response
    
    clinic = Clinic.query.get_or_404(clinic_id)
    doctors = Doctor.query.filter_by(clinic_id=clinic_id).all()
    
    if not doctors:
        flash('No doctors available at this clinic.', 'warning')
        return redirect(url_for('booking_bp.select_clinic'))
    
    return render_template('booking/select_doctor.html', clinic=clinic, doctors=doctors)

from datetime import date, timedelta

@booking_bp.route('/book/select-time/<int:doctor_id>')
def select_time(doctor_id):
    redirect_response = require_patient()
    if redirect_response:
        return redirect_response
    
    doctor = Doctor.query.get_or_404(doctor_id)

    today = date.today()
    available_slots = TimeSlot.query.filter(
        TimeSlot.doctor_id == doctor_id,
        TimeSlot.date >= today,
        TimeSlot.is_available == True
    ).order_by(TimeSlot.date, TimeSlot.start_time).limit(50).all()

    print(f"Doctor ID: {doctor_id}, Slots found: {len(available_slots)}")
    for slot in available_slots:
        print(f"{slot.date} {slot.start_time} - {slot.end_time} Available: {slot.is_available}")

    if not available_slots:
        flash('No available time slots for this doctor.', 'warning')
        return redirect(url_for('booking_bp.select_doctor', clinic_id=doctor.clinic_id))

    # Group time slots by date
    slots_by_date = defaultdict(list)
    for slot in available_slots:
        slots_by_date[slot.date].append(slot)

    return render_template('booking/select_time.html', doctor=doctor, slots_by_date=slots_by_date)


@booking_bp.route('/book/confirm/<int:time_slot_id>', methods=['GET', 'POST'])
def confirm_booking(time_slot_id):
    redirect_response = require_patient()
    if redirect_response:
        return redirect_response
    
    time_slot = TimeSlot.query.get_or_404(time_slot_id)
    doctor = Doctor.query.get(time_slot.doctor_id)
    
    if request.method == 'GET':
        if not time_slot.is_available:
            flash('This time slot is no longer available.', 'error')
            return redirect(url_for('booking_bp.select_time', doctor_id=doctor.id))
        return render_template('booking/confirmation.html', time_slot=time_slot, doctor=doctor)
    
    # POST method: actually book the appointment
    if not time_slot.is_available:
        flash('This time slot is no longer available.', 'error')
        return redirect(url_for('booking_bp.select_time', doctor_id=doctor.id))
    
    existing_appointment = Appointment.query.filter_by(
        patient_id=session['user_id'],
        time_slot_id=time_slot_id
    ).first()
    
    if existing_appointment:
        flash('You already have an appointment at this time.', 'error')
        return redirect(url_for('booking_bp.my_appointments'))
    
    appointment = Appointment(
        patient_id=session['user_id'],
        doctor_id=doctor.id,
        time_slot_id=time_slot_id,
        status='scheduled'
    )
    time_slot.is_available = False
    
    try:
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('booking_bp.booking_confirmation', appointment_id=appointment.id))
    except Exception:
        db.session.rollback()
        flash('An error occurred while booking your appointment. Please try again.', 'error')
        return redirect(url_for('booking_bp.select_time', doctor_id=doctor.id))



@booking_bp.route('/booking-confirmation/<int:appointment_id>', methods=['GET'])
def booking_confirmation(appointment_id):
    redirect_response = require_patient()
    if redirect_response:
        return redirect_response

    appointment = Appointment.query.get_or_404(appointment_id)
    time_slot = TimeSlot.query.get(appointment.time_slot_id)
    doctor = Doctor.query.get(time_slot.doctor_id)

    return render_template('booking/booking_confirmed.html', appointment=appointment, time_slot=time_slot, doctor=doctor)



@booking_bp.route('/my-appointments')
def my_appointments():
    redirect_response = require_patient()
    if redirect_response:
        return redirect_response
    
    appointments = Appointment.query.filter_by(
        patient_id=session['user_id']
    ).order_by(Appointment.created_at.desc()).all()
    
    return render_template('booking/my_appointments.html', appointments=appointments)

@booking_bp.route('/cancel-appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    redirect_response = require_patient()
    if redirect_response:
        return redirect_response
    
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=session['user_id']
    ).first_or_404()
    
    if appointment.status == 'cancelled':
        flash('This appointment is already cancelled.', 'warning')
        return redirect(url_for('booking_bp.my_appointments'))
    
    # Cancel the appointment and make time slot available again
    appointment.status = 'cancelled'
    if appointment.time_slot:
        appointment.time_slot.is_available = True
    
    try:
        db.session.commit()
        flash('Appointment cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while cancelling the appointment.', 'error')
    
    return redirect(url_for('booking_bp.my_appointments'))