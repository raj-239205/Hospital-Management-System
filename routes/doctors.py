from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .auth import login_required, role_required
from models import db, Doctor, Appointment, User

doctors_bp = Blueprint('doctors', __name__)

@doctors_bp.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    specialization_filter = request.args.get('specialization', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Doctor.query
    
    if search_query:
        query = query.filter(
            (Doctor.name.like(f"%{search_query}%")) |
            (Doctor.specialization.like(f"%{search_query}%")) |
            (Doctor.email.like(f"%{search_query}%"))
        )
        
    if specialization_filter:
        query = query.filter(Doctor.specialization == specialization_filter)
        
    pagination = query.order_by(Doctor.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    doctors = pagination.items
    
    # Get distinct specializations for filtering
    specializations = [d.specialization for d in db.session.query(Doctor.specialization).distinct().all()]
    
    return render_template('doctors/list.html', doctors=doctors, pagination=pagination, search_query=search_query, specialization_filter=specialization_filter, specializations=specializations)

@doctors_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')  # Only admin can add doctors
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        specialization = request.form.get('specialization')
        phone = request.form.get('phone')
        email = request.form.get('email')
        experience = request.form.get('experience')
        availability = request.form.get('availability', 'Available')
        
        # User details for auto-creating login
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validation
        if not name or not specialization or not phone or not email or not username or not password:
            flash('All fields including Login credentials are required.', 'danger')
            return render_template('doctors/form.html', action='Add', doctor=None)
            
        # Check if email or username already exists
        if Doctor.query.filter_by(email=email).first():
            flash('A doctor with this email already exists.', 'danger')
            return render_template('doctors/form.html', action='Add', doctor=None)
            
        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'danger')
            return render_template('doctors/form.html', action='Add', doctor=None)
            
        try:
            exp_val = int(experience) if experience else 0
        except ValueError:
            flash('Experience must be a number.', 'danger')
            return render_template('doctors/form.html', action='Add', doctor=None)
            
        # Create Doctor
        doctor = Doctor(
            name=name, specialization=specialization, phone=phone,
            email=email, experience=exp_val, availability=availability
        )
        db.session.add(doctor)
        db.session.flush() # Flush to get doctor.id
        
        # Create corresponding User
        user = User(username=username, role='doctor', doctor_id=doctor.id)
        user.set_password(password)
        db.session.add(user)
        
        db.session.commit()
        flash(f'Doctor Dr. {name} and user login created successfully!', 'success')
        return redirect(url_for('doctors.view', doctor_id=doctor.id))
        
    return render_template('doctors/form.html', action='Add', doctor=None)

@doctors_bp.route('/edit/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')  # Only admin can edit doctor details
def edit(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        specialization = request.form.get('specialization')
        phone = request.form.get('phone')
        email = request.form.get('email')
        experience = request.form.get('experience')
        availability = request.form.get('availability')
        
        if not name or not specialization or not phone or not email:
            flash('Please fill in all required fields.', 'danger')
            return render_template('doctors/form.html', action='Edit', doctor=doctor)
            
        # Check email conflict
        existing = Doctor.query.filter_by(email=email).first()
        if existing and existing.id != doctor.id:
            flash('This email is already registered to another doctor.', 'danger')
            return render_template('doctors/form.html', action='Edit', doctor=doctor)
            
        try:
            doctor.experience = int(experience) if experience else 0
        except ValueError:
            flash('Experience must be a number.', 'danger')
            return render_template('doctors/form.html', action='Edit', doctor=doctor)
            
        doctor.name = name
        doctor.specialization = specialization
        doctor.phone = phone
        doctor.email = email
        doctor.availability = availability
        
        db.session.commit()
        flash('Doctor details updated successfully!', 'success')
        return redirect(url_for('doctors.view', doctor_id=doctor.id))
        
    return render_template('doctors/form.html', action='Edit', doctor=doctor)

@doctors_bp.route('/view/<int:doctor_id>')
@login_required
def view(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Associated user
    associated_user = User.query.filter_by(doctor_id=doctor_id).first()
    
    # Doctor's appointments
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    return render_template('doctors/profile.html', doctor=doctor, user=associated_user, appointments=appointments)

@doctors_bp.route('/delete/<int:doctor_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Delete associated user first
    user = User.query.filter_by(doctor_id=doctor_id).first()
    if user:
        db.session.delete(user)
        
    db.session.delete(doctor)
    db.session.commit()
    flash('Doctor and their login account deleted successfully.', 'success')
    return redirect(url_for('doctors.index'))
