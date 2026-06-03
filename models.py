from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='patient')  # 'admin', 'doctor', 'patient'
    
    # User Profile additions
    email = db.Column(db.String(100), unique=True, nullable=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True, default='default_avatar.png')
    
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True)
    
    doctor = db.relationship('Doctor', backref=db.backref('user', uselist=False))
    patient = db.relationship('Patient', backref=db.backref('user', uselist=False))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    experience = db.Column(db.Integer, nullable=False, default=0)
    availability = db.Column(db.String(100), nullable=False, default='Available') # "Available" or "Unavailable"
    
    appointments = db.relationship('Appointment', backref='doctor', cascade="all, delete-orphan", lazy=True)

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)  # Auto incremented Patient ID
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    blood_group = db.Column(db.String(10), nullable=True)
    disease = db.Column(db.String(100), nullable=True)
    admission_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Outpatient')  # 'Admitted', 'Discharged', 'Outpatient'
    
    appointments = db.relationship('Appointment', backref='patient', cascade="all, delete-orphan", lazy=True)
    bills = db.relationship('Bill', backref='patient', cascade="all, delete-orphan", lazy=True)
    rooms = db.relationship('Room', backref='assigned_patient', foreign_keys='Room.assigned_patient_id')

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(20), nullable=False) # e.g. "10:30 AM"
    status = db.Column(db.String(20), nullable=False, default='Scheduled')  # 'Scheduled', 'Completed', 'Cancelled'

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    date_written = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    symptoms = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=True)
    medications = db.Column(db.Text, nullable=False)  # List of medicines and dosages
    instructions = db.Column(db.Text, nullable=True)   # Advice / instructions
    
    patient = db.relationship('Patient', backref='prescriptions')
    doctor = db.relationship('Doctor', backref='prescriptions')

class Bill(db.Model):
    __tablename__ = 'bills'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    consultation_charges = db.Column(db.Float, nullable=False, default=0.0)
    medicine_charges = db.Column(db.Float, nullable=False, default=0.0)
    room_charges = db.Column(db.Float, nullable=False, default=0.0)
    gst_rate = db.Column(db.Float, nullable=False, default=18.0) # percentage (18%)
    total_amount = db.Column(db.Float, nullable=False)
    invoice_pdf_path = db.Column(db.String(255), nullable=True)
    date_generated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Medicine(db.Model):
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0.0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=10)

class Room(db.Model):
    __tablename__ = 'rooms'
    
    room_number = db.Column(db.String(20), primary_key=True)
    room_type = db.Column(db.String(50), nullable=False)  # 'General', 'Private', 'ICU', 'Semi-Private'
    availability_status = db.Column(db.Boolean, nullable=False, default=True)
    assigned_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True)

class UserActivity(db.Model):
    __tablename__ = 'user_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True) # Nullable for guests
    username = db.Column(db.String(80), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref='activities')
