from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from .auth import login_required, role_required
from models import db, Patient, Appointment, Bill, Room

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/')
@login_required
def index():
    if session.get('role') == 'patient':
        return redirect(url_for('patients.view', patient_id=session.get('patient_id')))
        
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    gender_filter = request.args.get('gender', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Patient.query
    
    if search_query:
        query = query.filter(
            (Patient.name.like(f"%{search_query}%")) | 
            (Patient.id.like(f"%{search_query}%")) |
            (Patient.phone_number.like(f"%{search_query}%"))
        )
        
    if status_filter:
        query = query.filter(Patient.status == status_filter)
        
    if gender_filter:
        query = query.filter(Patient.gender == gender_filter)
        
    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Patient.admission_date >= df)
        except ValueError:
            pass
            
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Patient.admission_date <= dt)
        except ValueError:
            pass
        
    # Order by admission date descending
    pagination = query.order_by(Patient.admission_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    patients = pagination.items
    
    # Calculate Patient Analytics Counts
    total_patients_count = Patient.query.count()
    outpatients_count = Patient.query.filter_by(status='Outpatient').count()
    inpatients_count = Patient.query.filter_by(status='Admitted').count()
    discharged_count = Patient.query.filter_by(status='Discharged').count()
    
    return render_template(
        'patients/list.html', 
        patients=patients, 
        pagination=pagination, 
        search_query=search_query, 
        status_filter=status_filter,
        gender_filter=gender_filter,
        date_from=date_from,
        date_to=date_to,
        total_patients_count=total_patients_count,
        outpatients_count=outpatients_count,
        inpatients_count=inpatients_count,
        discharged_count=discharged_count
    )

@patients_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if session.get('role') == 'patient':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        blood_group = request.form.get('blood_group')
        disease = request.form.get('disease')
        admission_date_str = request.form.get('admission_date')
        status = request.form.get('status', 'Admitted')
        
        # Simple Validation
        if not name or not age or not gender or not phone_number or not address:
            flash('Please fill in all required fields.', 'danger')
            return render_template('patients/form.html', action='Add', patient=None)
            
        try:
            age = int(age)
            if age < 0:
                raise ValueError("Age must be positive.")
        except ValueError:
            flash('Please enter a valid age.', 'danger')
            return render_template('patients/form.html', action='Add', patient=None)
            
        admission_date = datetime.strptime(admission_date_str, '%Y-%m-%d').date() if admission_date_str else datetime.utcnow().date()
        
        patient = Patient(
            name=name, age=age, gender=gender, phone_number=phone_number,
            address=address, blood_group=blood_group, disease=disease,
            admission_date=admission_date, status=status
        )
        
        db.session.add(patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients.view', patient_id=patient.id))
        
    # Render Add Form
    today = datetime.utcnow().date().strftime('%Y-%m-%d')
    return render_template('patients/form.html', action='Add', today=today, patient=None)

@patients_bp.route('/edit/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit(patient_id):
    if session.get('role') == 'patient' and patient_id != session.get('patient_id'):
        flash('Unauthorized access: You can only edit your own details.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        blood_group = request.form.get('blood_group')
        disease = request.form.get('disease')
        admission_date_str = request.form.get('admission_date')
        status = request.form.get('status')
        
        # Validation
        if not name or not age or not gender or not phone_number or not address:
            flash('Please fill in all required fields.', 'danger')
            return render_template('patients/form.html', action='Edit', patient=patient)
            
        try:
            patient.age = int(age)
        except ValueError:
            flash('Please enter a valid age.', 'danger')
            return render_template('patients/form.html', action='Edit', patient=patient)
            
        patient.name = name
        patient.gender = gender
        patient.phone_number = phone_number
        patient.address = address
        patient.blood_group = blood_group
        patient.disease = disease
        patient.status = status
        
        if admission_date_str:
            patient.admission_date = datetime.strptime(admission_date_str, '%Y-%m-%d').date()
            
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('patients.view', patient_id=patient.id))
        
    # Render Edit Form
    admission_date_str = patient.admission_date.strftime('%Y-%m-%d') if patient.admission_date else ''
    return render_template('patients/form.html', action='Edit', patient=patient, admission_date_str=admission_date_str)

@patients_bp.route('/view/<int:patient_id>')
@login_required
def view(patient_id):
    if session.get('role') == 'patient' and patient_id != session.get('patient_id'):
        flash('Unauthorized access: You can only view your own details.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    patient = Patient.query.get_or_404(patient_id)
    
    # Get appointments for this patient
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.appointment_date.desc()).all()
    
    # Get billing history
    bills = Bill.query.filter_by(patient_id=patient_id).order_by(Bill.date_generated.desc()).all()
    
    # Get room details
    room = Room.query.filter_by(assigned_patient_id=patient_id).first()
    
    return render_template('patients/profile.html', patient=patient, appointments=appointments, bills=bills, room=room)

@patients_bp.route('/delete/<int:patient_id>', methods=['POST'])
@login_required
@role_required('admin')  # Only admin can delete patients
def delete(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Free up room if assigned
    room = Room.query.filter_by(assigned_patient_id=patient_id).first()
    if room:
        room.assigned_patient_id = None
        room.availability_status = True
        
    db.session.delete(patient)
    db.session.commit()
    flash('Patient deleted successfully.', 'success')
    return redirect(url_for('patients.index'))
