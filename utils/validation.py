import re
from datetime import datetime, date

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if not password:
        return False
    
    # Minimum 6 characters
    if len(password) < 6:
        return False
    
    return True

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's 10 digits long
    return len(digits_only) == 10

def validate_name(name):
    """Validate name format"""
    if not name:
        return False
    
    # Name should contain only letters and spaces
    pattern = r'^[a-zA-Z\s]+$'
    return re.match(pattern, name.strip()) is not None and len(name.strip()) >= 2

def validate_age(age):
    """Validate age"""
    if age is None:
        return True  # Age is optional
    
    try:
        age_int = int(age)
        return 1 <= age_int <= 120
    except (ValueError, TypeError):
        return False

def validate_date(date_str):
    """Validate date format (YYYY-MM-DD)"""
    if not date_str:
        return False
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_time(time_str):
    """Validate time format (HH:MM)"""
    if not time_str:
        return False
    
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def validate_future_date(date_str):
    """Validate that date is in the future"""
    if not validate_date(date_str):
        return False
    
    try:
        input_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return input_date >= date.today()
    except ValueError:
        return False

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    text = text.strip()
    text = re.sub(r'[<>"\']', '', text)
    
    return text

def validate_blood_group(blood_group):
    """Validate blood group"""
    if not blood_group:
        return True  # Blood group is optional
    
    valid_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    return blood_group.upper() in valid_groups

def validate_gender(gender):
    """Validate gender"""
    if not gender:
        return True  # Gender is optional
    
    valid_genders = ['male', 'female', 'other']
    return gender.lower() in valid_genders
