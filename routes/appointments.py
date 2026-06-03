from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from .auth import login_required
from models import db, Appointment, Patient, Doctor

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    doctor_filter = request.args.get('doctor_id', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Appointment.query
    
    # Role check: doctors see only their appointments
    if session.get('role') == 'doctor':
        query = query.filter(Appointment.doctor_id == session.get('doctor_id'))
    elif doctor_filter:
        query = query.filter(Appointment.doctor_id == doctor_filter)
        
    if search_query:
        # Search by patient name
        query = query.join(Patient).filter(Patient.name.like(f"%{search_query}%"))
        
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
        
    pagination = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).paginate(page=page, per_page=per_page, error_out=False)
    appointments = pagination.items
    
    doctors = Doctor.query.all()
    
    return render_template('appointments/list.html', appointments=appointments, pagination=pagination, search_query=search_query, status_filter=status_filter, doctor_filter=doctor_filter, doctors=doctors)

@appointments_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        date_str = request.form.get('appointment_date')
        time_str = request.form.get('appointment_time')
        status = request.form.get('status', 'Scheduled')
        
        if not patient_id or not doctor_id or not date_str or not time_str:
            flash('Please select patient, doctor, date, and time.', 'danger')
            return redirect(url_for('appointments.book'))
            
        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('appointments.book'))
            
        # Check doctor availability
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            flash('Selected doctor not found.', 'danger')
            return redirect(url_for('appointments.book'))
            
        # Optional: check if doctor has appointment at the exact time
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id, 
            appointment_date=appt_date, 
            appointment_time=time_str,
            status='Scheduled'
        ).first()
        
        if existing:
            flash(f'Dr. {doctor.name} is already booked at {time_str} on {date_str}.', 'warning')
            
        appointment = Appointment(
            patient_id=patient_id, doctor_id=doctor_id,
            appointment_date=appt_date, appointment_time=time_str,
            status=status
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('appointments.index'))
        
    patients = Patient.query.filter(Patient.status != 'Discharged').all()
    doctors = Doctor.query.filter_by(availability='Available').all()
    today = datetime.utcnow().date().strftime('%Y-%m-%d')
    
    # Pre-select patient if ID is passed
    pre_selected_patient_id = request.args.get('patient_id', type=int)
    
    return render_template('appointments/book.html', patients=patients, doctors=doctors, today=today, pre_selected_patient_id=pre_selected_patient_id)

@appointments_bp.route('/update-status/<int:appointment_id>', methods=['POST'])
@login_required
def update_status(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    new_status = request.form.get('status')
    
    if new_status in ['Scheduled', 'Completed', 'Cancelled']:
        appointment.status = new_status
        db.session.commit()
        flash(f'Appointment status updated to {new_status}.', 'success')
    else:
        flash('Invalid status value.', 'danger')
        
    return redirect(request.referrer or url_for('appointments.index'))

@appointments_bp.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Role restriction if necessary (e.g. only doctor assigned or admin)
    if session.get('role') == 'doctor' and appointment.doctor_id != session.get('doctor_id'):
        flash('You can only cancel your own appointments.', 'danger')
        return redirect(url_for('appointments.index'))
        
    appointment.status = 'Cancelled'
    db.session.commit()
    flash('Appointment has been cancelled.', 'warning')
    return redirect(request.referrer or url_for('appointments.index'))
