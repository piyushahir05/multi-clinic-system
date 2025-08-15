from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from local_models import Doctor, TimeSlot, Appointment,Patient
from local_db import db
from datetime import datetime, date, time
from sqlalchemy.orm import aliased
from sqlalchemy import or_, and_

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
    
    stats = {
        'today_appointments': len(today_appointments),
        'total_appointments': total_appointments,
        'patients_seen': total_appointments - pending_appointments,
        'pending_appointments': pending_appointments
    }

    return render_template('doctor/dashboard.html',
                         doctor=doctor,
                         today_appointments=today_appointments,
                         upcoming_appointments=upcoming_appointments,
                         total_appointments=total_appointments,
                         pending_appointments=pending_appointments,
                         stats=stats)

@doctor_bp.route('/doctor/appointments')
def appointments():
    redirect_response = require_doctor()
    if redirect_response:
        return redirect_response

    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth_bp.logout'))

    # Get filter parameters from query string
    status_filter = request.args.get('status', '')  # '' means no filter (all)
    date_filter = request.args.get('date', '')      # expected format: 'YYYY-MM-DD'
    search = request.args.get('search', '').strip() # patient name/email/phone search

    # Base query for this doctor's appointments
    query = Appointment.query.filter_by(doctor_id=doctor.id)

    # Apply status filter if given
    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    # Apply date filter if given
    if date_filter:
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
            # Assuming Appointment has a relation to TimeSlot with a date field
            query = query.join(Appointment.time_slot).filter(TimeSlot.date == date_obj)
        except ValueError:
            # Invalid date format, ignore filter or flash message if you want
            pass

    # Apply patient search filter if given
    if search:
        # Join with Patient to filter by name, email, or phone
        query = query.join(Appointment.patient).filter(
            (Patient.name.ilike(f'%{search}%')) |
            (Patient.email.ilike(f'%{search}%')) |
            (Patient.phone.ilike(f'%{search}%'))
        )

    # Order by creation time descending
    query = query.order_by(Appointment.created_at.desc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    appointments = query.paginate(page=page, per_page=10)

    return render_template('doctor/appointments.html',
                           doctor=doctor,
                           appointments=appointments,
                           status=status_filter,
                           date_filter=date_filter,
                           search=search)



@doctor_bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    redirect_response = require_doctor()
    if redirect_response:
        return redirect_response

    doctor = get_doctor_profile()
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first_or_404()

    if appointment.status == 'cancelled':
        flash('This appointment is already cancelled.', 'warning')
        return redirect(url_for('doctor_bp.appointments'))

    appointment.status = 'cancelled'
    if appointment.time_slot:
        appointment.time_slot.is_available = True

    try:
        db.session.commit()
        flash('Appointment cancelled successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('An error occurred while cancelling the appointment.', 'error')

    return redirect(url_for('doctor_bp.appointments'))




@doctor_bp.route('/doctor/schedule', methods=['GET', 'POST'])
def schedule():
    redirect_response = require_doctor()
    if redirect_response:
        return redirect_response

    doctor = get_doctor_profile()
    if not doctor:
        flash('Doctor profile not found.', 'error')
        return redirect(url_for('auth_bp.logout'))
    today = date.today()

    query = TimeSlot.query.filter(
    TimeSlot.doctor_id == doctor.id,
    TimeSlot.date >= today  # only future and today dates
)

    # Fetch filters from GET request
    date_filter = request.args.get('date')
    availability = request.args.get('availability')

    AppointmentAlias = aliased(Appointment)

   
    query = db.session.query(TimeSlot).outerjoin(
    AppointmentAlias, TimeSlot.id == AppointmentAlias.time_slot_id
).filter(
    TimeSlot.doctor_id == doctor.id,
    TimeSlot.date >= today,  # exclude past dates here
    or_(
        TimeSlot.is_available == True,
        and_(
            TimeSlot.is_available == False,
            AppointmentAlias.status != 'completed'
        )
    )
)

    if date_filter:
        try:
            date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(TimeSlot.date == date_obj)
        except ValueError:
            flash('Invalid date format.', 'error')

    if availability == 'available':
        query = query.filter_by(is_available=True)
    elif availability == 'booked':
        query = query.filter_by(is_available=False)

    page = request.args.get('page', 1, type=int)
    per_page = 10  # or whatever you want

    time_slots = query.order_by(TimeSlot.date, TimeSlot.start_time).paginate(page=page, per_page=per_page)


    # Handle time slot creation if POST
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')

        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()

        if not all([date_str, start_time, end_time]):
            flash('All fields are required.', 'error')
            return render_template('doctor/schedule.html', doctor=doctor, time_slots=time_slots, date_filter=date_filter, availability=availability)

        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            existing_slot = TimeSlot.query.filter_by(
                doctor_id=doctor.id,
                date=appointment_date,
                start_time=start_time,
                end_time=end_time
            ).first()

            if existing_slot:
                flash('A time slot already exists for this date and time.', 'warning')
            else:
                new_slot = TimeSlot(
                    doctor_id=doctor.id,
                    date=appointment_date,
                    start_time=start_time,
                    end_time=end_time,
                    is_available=True
                )
                db.session.add(new_slot)
                db.session.commit()
                flash('Time slot added successfully!', 'success')
                return redirect(url_for('doctor_bp.schedule'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the time slot.', 'error')

    return render_template('doctor/schedule.html', doctor=doctor, time_slots=time_slots, date_filter=date_filter, availability=availability)





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