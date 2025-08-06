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
            return redirect(url_for('admin.manage_clinics'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the clinic.', 'error')
            return render_template('admin/add_clinic.html')

    # If GET request, render the form
    return render_template('admin/add_clinic.html')



@admin_bp.route('/admin/clinics/edit/<int:clinic_id>', methods=['GET', 'POST'])
def edit_clinic(clinic_id):
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response

    clinic = Clinic.query.get_or_404(clinic_id)

    if request.method == 'POST':
        clinic.name = request.form.get('name')
        clinic.address = request.form.get('address')
        clinic.phone = request.form.get('phone')
        clinic.email = request.form.get('email')

        try:
            db.session.commit()
            flash('Clinic updated successfully!', 'success')
            return redirect(url_for('admin_bp.manage_clinics'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the clinic.', 'error')

    # Instead of edit_clinic.html, reuse manage_clinics.html and pass context for edit
    clinics = Clinic.query.all()
    return render_template('admin/manage_clinics.html', clinics=clinics, editing_clinic=clinic)




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
        if User.query.filter_by(email=email.lower().strip()).first():
            flash('A user with this email already exists.', 'error')
            return render_template('admin/add_doctor.html', clinics=clinics)

        # Create the user
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            phone=phone.strip() if phone else None,
            role='doctor'
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.flush()  # So user.id becomes available

            # Create the doctor profile
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

    return render_template('admin/add_doctor.html', clinics=clinics)



@admin_bp.route('/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    user = doctor.user
    clinics = Clinic.query.all()

    if request.method == 'POST':
        # Update user-related fields
        user.name = request.form['name']
        user.email = request.form['email']
        user.phone = request.form['phone']

        # Update doctor-specific fields
        doctor.specialization = request.form['specialization']
        doctor.license_number = request.form['license_number']
        doctor.years_experience = int(request.form['years_experience']) if request.form['years_experience'] else None
        doctor.clinic_id = int(request.form['clinic_id'])

        try:
            db.session.commit()
            flash('Doctor details updated successfully.', 'success')
            return redirect(url_for('admin_bp.manage_doctors'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating doctor: ' + str(e), 'danger')

    return render_template('admin/edit_doctor.html', doctor=doctor, clinics=clinics)



@admin_bp.route('/delete_doctor/<int:doctor_id>', methods=['POST'])
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    user = doctor.user

    # Check if the doctor has any scheduled appointments
    scheduled_appointments = [appt for appt in doctor.appointments if appt.status == 'scheduled']
    if scheduled_appointments:
        flash("Cannot delete doctor with scheduled appointments.", "warning")
        return redirect(url_for('admin_bp.manage_doctors'))

    try:
        db.session.delete(doctor)
        db.session.delete(user)  # Remove linked user account as well
        db.session.commit()
        flash(f"Doctor {user.name} deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash('Error deleting doctor: ' + str(e), 'danger')

    return redirect(url_for('admin_bp.manage_doctors'))




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

@admin_bp.route('/delete_time_slot/<int:slot_id>', methods=['POST'])
def delete_time_slot(slot_id):
    flash(f"Delete route not implemented yet (slot ID: {slot_id})", "info")
    return redirect(url_for('admin_bp.manage_time_slots'))
