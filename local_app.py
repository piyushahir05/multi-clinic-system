import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)

# Set up logging for development
logging.basicConfig(level=logging.DEBUG)

# Configuration for local development
app.secret_key = os.environ.get("SESSION_SECRET", "your-local-secret-key-for-development-only")

# For local development, we'll use SQLite which creates a local database file
# This is much easier than setting up PostgreSQL locally
database_url = os.environ.get("DATABASE_URL")
if not database_url or database_url.startswith("postgresql://"):
    # Use SQLite for local development - creates clinic_appointments.db file
    database_url = "sqlite:///clinic_appointments.db"
    
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import all routes
from routes.auth import auth_bp
from routes.booking import booking_bp
from routes.admin import admin_bp
from routes.doctor import doctor_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(doctor_bp)

with app.app_context():
    # Import models to create tables
    import models
    
    # Create all tables
    db.create_all()
    
    # Create default admin user if it doesn't exist
    from models import User
    from werkzeug.security import generate_password_hash
    
    admin_user = User.query.filter_by(email='admin@clinic.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@clinic.com',
            name='System Administrator',
            phone='555-0123',
            role='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin user created: admin@clinic.com / admin123")
    
    # Create sample clinic and doctor if they don't exist
    from models import Clinic, Doctor
    
    sample_clinic = Clinic.query.filter_by(name='General Medical Center').first()
    if not sample_clinic:
        sample_clinic = Clinic(
            name='General Medical Center',
            address='123 Health Street, Medical City',
            phone='555-0100',
            email='info@generalmedical.com'
        )
        db.session.add(sample_clinic)
        db.session.commit()
        print("Sample clinic created: General Medical Center")
    
    # Create sample doctor user and doctor profile
    doctor_user = User.query.filter_by(email='doctor@clinic.com').first()
    if not doctor_user:
        doctor_user = User(
            email='doctor@clinic.com',
            name='Dr. Sarah Johnson',
            phone='555-0124',
            role='doctor',
            password_hash=generate_password_hash('doctor123')
        )
        db.session.add(doctor_user)
        db.session.commit()
        
        # Create doctor profile
        doctor_profile = Doctor(
            user_id=doctor_user.id,
            clinic_id=sample_clinic.id,
            specialization='General Medicine',
            license_number='MD123456',
            years_experience=8
        )
        db.session.add(doctor_profile)
        db.session.commit()
        print("Sample doctor created: doctor@clinic.com / doctor123")
        
        # Create some sample time slots
        from models import TimeSlot
        from datetime import datetime, timedelta
        
        # Create time slots for the next 7 days
        for day_offset in range(7):
            date = datetime.now().date() + timedelta(days=day_offset)
            
            # Morning slots (9 AM to 12 PM)
            for hour in range(9, 12):
                time_slot = TimeSlot(
                    doctor_id=doctor_profile.id,
                    date=date,
                    start_time=f"{hour:02d}:00",
                    end_time=f"{hour+1:02d}:00",
                    is_available=True
                )
                db.session.add(time_slot)
            
            # Afternoon slots (2 PM to 5 PM)  
            for hour in range(14, 17):
                time_slot = TimeSlot(
                    doctor_id=doctor_profile.id,
                    date=date,
                    start_time=f"{hour:02d}:00",
                    end_time=f"{hour+1:02d}:00",
                    is_available=True
                )
                db.session.add(time_slot)
        
        db.session.commit()
        print("Sample time slots created for Dr. Sarah Johnson")

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    from flask import render_template
    app.run(host='127.0.0.1', port=5000, debug=True)