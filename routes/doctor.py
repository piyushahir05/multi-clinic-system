from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from models import Doctor, TimeSlot, Appointment
from app import db
from datetime import datetime, date, time

doctor_bp = Blueprint('doctor_bp', __name__)

def require_doctor():
    if 'user_id' not in session or session.get('user_role') != 'doctor':
        return redirect(url_for('auth_bp.login'))
    return None

def get_doctor_profile():
    if 'user_id' not in session:
        return None
    return Doctor.query.filter_by(user_id=session['user_id']).first()

@doctor_bp.route('/dashboard')
def dashboard():
    auth_check = require_doctor()
    if auth_check:
        return auth_check
    
    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('auth_bp.logout'))
    
    # Get upcoming appointments
    today = date.today()
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.time_slot.has(TimeSlot.date >= today)
    ).order_by(Appointment.time_slot.has(TimeSlot.date), Appointment.time_slot.has(TimeSlot.start_time)).limit(10).all()
    
    # Get today's appointments
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.time_slot.has(TimeSlot.date == today)
    ).order_by(Appointment.time_slot.has(TimeSlot.start_time)).all()
    
    # Get statistics
    stats = {
        'total_appointments': Appointment.query.filter_by(doctor_id=doctor.id).count(),
        'today_appointments': len(today_appointments),
        'upcoming_appointments': len(upcoming_appointments),
        'available_slots': TimeSlot.query.filter_by(doctor_id=doctor.id, is_available=True).count()
    }
    
    return render_template('doctor_dashboard.html', 
                         doctor=doctor, 
                         upcoming_appointments=upcoming_appointments,
                         today_appointments=today_appointments,
                         stats=stats)

@doctor_bp.route('/appointments')
def appointments():
    auth_check = require_doctor()
    if auth_check:
        return auth_check
    
    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('auth_bp.logout'))
    
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.created_at.desc()).all()
    
    return render_template('doctor_dashboard.html', section='appointments', appointments=appointments)

@doctor_bp.route('/api/appointments')
def api_appointments():
    auth_check = require_doctor()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    doctor = get_doctor_profile()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404
    
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.created_at.desc()).all()
    return jsonify([appointment.to_dict() for appointment in appointments])

@doctor_bp.route('/schedule')
def schedule():
    auth_check = require_doctor()
    if auth_check:
        return auth_check
    
    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found', 'error')
        return redirect(url_for('auth_bp.logout'))
    
    # Get all time slots for the doctor
    slots = TimeSlot.query.filter_by(doctor_id=doctor.id).order_by(TimeSlot.date.desc(), TimeSlot.start_time.desc()).all()
    
    return render_template('doctor_dashboard.html', section='schedule', slots=slots)

@doctor_bp.route('/api/slots', methods=['GET', 'POST'])
def api_slots():
    auth_check = require_doctor()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    doctor = get_doctor_profile()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404
    
    if request.method == 'POST':
        data = request.get_json()
        
        required_fields = ['date', 'start_time', 'end_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        try:
            slot_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            
            # Validate that the slot is in the future
            if slot_date < date.today():
                return jsonify({'success': False, 'message': 'Cannot create slots for past dates'}), 400
            
            if start_time >= end_time:
                return jsonify({'success': False, 'message': 'Start time must be before end time'}), 400
            
            # Check for conflicting slots
            existing_slot = TimeSlot.query.filter(
                TimeSlot.doctor_id == doctor.id,
                TimeSlot.date == slot_date,
                TimeSlot.start_time < end_time,
                TimeSlot.end_time > start_time
            ).first()
            
            if existing_slot:
                return jsonify({'success': False, 'message': 'Time slot conflicts with existing slot'}), 400
            
            slot = TimeSlot(
                doctor_id=doctor.id,
                date=slot_date,
                start_time=start_time,
                end_time=end_time,
                is_available=True
            )
            
            db.session.add(slot)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Time slot added successfully', 'slot': slot.to_dict()})
            
        except ValueError as e:
            return jsonify({'success': False, 'message': 'Invalid date or time format'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Failed to add time slot'}), 500
    
    # GET request
    slots = TimeSlot.query.filter_by(doctor_id=doctor.id).order_by(TimeSlot.date.desc(), TimeSlot.start_time.desc()).all()
    return jsonify([slot.to_dict() for slot in slots])

@doctor_bp.route('/api/slots/<int:slot_id>', methods=['DELETE'])
def api_delete_slot(slot_id):
    auth_check = require_doctor()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    doctor = get_doctor_profile()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404
    
    slot = TimeSlot.query.filter_by(id=slot_id, doctor_id=doctor.id).first()
    if not slot:
        return jsonify({'success': False, 'message': 'Time slot not found'}), 404
    
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

@doctor_bp.route('/api/appointments/<int:appointment_id>/status', methods=['PUT'])
def update_appointment_status(appointment_id):
    auth_check = require_doctor()
    if auth_check:
        return jsonify({'error': 'Unauthorized'}), 401
    
    doctor = get_doctor_profile()
    if not doctor:
        return jsonify({'error': 'Doctor profile not found'}), 404
    
    appointment = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor.id).first()
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found'}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['scheduled', 'completed', 'cancelled']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    try:
        appointment.status = new_status
        appointment.notes = data.get('notes', appointment.notes)
        
        # If appointment is cancelled, make the slot available again
        if new_status == 'cancelled':
            appointment.time_slot.is_available = True
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Appointment status updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update appointment status'}), 500
