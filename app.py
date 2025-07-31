import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
database_url = os.environ.get("DATABASE_URL", "sqlite:///clinic_system.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Import models to ensure tables are created
from models import User, Clinic, Doctor, TimeSlot, Appointment

# Register blueprints
from routes.auth import auth_bp
from routes.booking import booking_bp
from routes.admin import admin_bp
from routes.doctor import doctor_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(booking_bp, url_prefix='/booking')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(doctor_bp, url_prefix='/doctor')

# Main routes
from flask import render_template, session, redirect, url_for

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))
    
    user_role = session.get('user_role')
    if user_role == 'admin':
        return redirect(url_for('admin_bp.dashboard'))
    elif user_role == 'doctor':
        return redirect(url_for('doctor_bp.dashboard'))
    elif user_role == 'patient':
        return redirect(url_for('booking_bp.select_clinic'))
    
    return redirect(url_for('home'))

with app.app_context():
    db.create_all()
    
    # Create default admin user if it doesn't exist
    from werkzeug.security import generate_password_hash
    admin_user = User.query.filter_by(email='admin@clinic.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@clinic.com',
            username='admin',
            full_name='System Administrator',
            role='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin_user)
        db.session.commit()
        logging.info("Default admin user created: admin@clinic.com / admin123")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
