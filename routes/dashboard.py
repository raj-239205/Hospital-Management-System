from flask import Blueprint, render_template, session, redirect, url_for
from .auth import login_required
from models import db, Patient, Doctor, Appointment, Bill, Medicine, Room, UserActivity, Prescription
from sqlalchemy import func
from datetime import datetime, date

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def home():
    from flask import session
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')

@dashboard_bp.route('/dashboard')
@login_required
def index():
    role = session.get('role')
    doctor_id = session.get('doctor_id')
    patient_id = session.get('patient_id')
    
    # Base statistics (shared or administrative)
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()
    
    revenue_sum = db.session.query(func.sum(Bill.total_amount)).scalar()
    total_revenue = round(revenue_sum, 2) if revenue_sum else 0.0
    low_stock_medicines = Medicine.query.filter(Medicine.stock <= Medicine.low_stock_threshold).count()
    available_rooms = Room.query.filter_by(availability_status=True).count()
    
    # 1. Patient Portal
    if role == 'patient':
        patient = Patient.query.get_or_404(patient_id)
        upcoming_appointments = Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.status == 'Scheduled'
        ).order_by(Appointment.appointment_date.asc()).all()
        
        my_prescriptions = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.date_written.desc()).limit(5).all()
        my_bills = Bill.query.filter_by(patient_id=patient_id).order_by(Bill.date_generated.desc()).limit(5).all()
        
        # Calculate summary numbers for patient
        total_spent = sum(bill.total_amount for bill in my_bills)
        
        return render_template('dashboard.html',
                               patient=patient,
                               upcoming_appointments=upcoming_appointments,
                               my_prescriptions=my_prescriptions,
                               my_bills=my_bills,
                               total_spent=total_spent,
                               total_patients=total_patients,
                               total_doctors=total_doctors,
                               total_appointments=total_appointments,
                               total_revenue=total_revenue,
                               available_rooms=available_rooms,
                               is_patient=True)
                               
    # 2. Doctor Portal
    elif role == 'doctor':
        doctor = Doctor.query.get_or_404(doctor_id)
        
        # Today's appointments (Scheduled)
        today_val = date.today()
        todays_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == today_val,
            Appointment.status == 'Scheduled'
        ).order_by(Appointment.appointment_time.asc()).all()
        
        all_my_appointments = Appointment.query.filter_by(doctor_id=doctor_id).all()
        my_appointments_count = len(all_my_appointments)
        my_completed_appointments = sum(1 for appt in all_my_appointments if appt.status == 'Completed')
        my_pending_appointments = sum(1 for appt in all_my_appointments if appt.status == 'Scheduled')
        
        # Unique assigned patients (patients this doctor has appointments with)
        assigned_patient_ids = db.session.query(Appointment.patient_id).filter_by(doctor_id=doctor_id).distinct().all()
        assigned_patients_count = len(assigned_patient_ids)
        
        # Upcoming schedule (next 10 days)
        upcoming_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date >= today_val,
            Appointment.status == 'Scheduled'
        ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).limit(5).all()
        
        my_prescriptions = Prescription.query.filter_by(doctor_id=doctor_id).order_by(Prescription.date_written.desc()).limit(5).all()
        
        return render_template('dashboard.html',
                               doctor=doctor,
                               todays_appointments=todays_appointments,
                               upcoming_appointments=upcoming_appointments,
                               my_appointments_count=my_appointments_count,
                               my_completed_appointments=my_completed_appointments,
                               my_pending_appointments=my_pending_appointments,
                               assigned_patients_count=assigned_patients_count,
                               my_prescriptions=my_prescriptions,
                               total_patients=total_patients,
                               total_doctors=total_doctors,
                               total_appointments=total_appointments,
                               total_revenue=total_revenue,
                               available_rooms=available_rooms,
                               is_doctor=True)
                               
    # 3. Admin Portal
    else:
        # Admin statistics & recent activities
        recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()
        recent_appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
        recent_bills = Bill.query.order_by(Bill.id.desc()).limit(5).all()
        
        # Audit Logs from UserActivity
        audit_activities = UserActivity.query.order_by(UserActivity.timestamp.desc()).limit(8).all()
        
        recent_activities = []
        for p in recent_patients:
            recent_activities.append({
                'type': 'Admission',
                'badge_class': 'bg-success',
                'desc': f"New Patient '{p.name}' admitted (Status: {p.status})",
                'time': datetime.combine(p.admission_date, datetime.min.time())
            })
            
        for appt in recent_appointments:
            recent_activities.append({
                'type': 'Appointment',
                'badge_class': 'bg-primary',
                'desc': f"Appointment booked: {appt.patient.name} with Dr. {appt.doctor.name}",
                'time': datetime.combine(appt.appointment_date, datetime.min.time())
            })
            
        for bill in recent_bills:
            recent_activities.append({
                'type': 'Invoice',
                'badge_class': 'bg-warning text-dark',
                'desc': f"Bill generated for {bill.patient.name} - Total: ${bill.total_amount:.2f}",
                'time': bill.date_generated
            })
            
        # Combine database actions with system log activity actions
        for act in audit_activities:
            # Avoid repeating
            recent_activities.append({
                'type': 'Audit Log',
                'badge_class': 'bg-secondary',
                'desc': f"User '{act.username}' performed action: '{act.action}' ({act.details or ''})",
                'time': act.timestamp
            })
            
        # Sort recent activities by time descending
        recent_activities.sort(key=lambda x: x['time'], reverse=True)
        recent_activities = recent_activities[:10]
        
        return render_template('dashboard.html', 
                               total_patients=total_patients,
                               total_doctors=total_doctors,
                               total_appointments=total_appointments,
                               total_revenue=total_revenue,
                               low_stock_medicines=low_stock_medicines,
                               available_rooms=available_rooms,
                               recent_activities=recent_activities,
                               is_doctor=False,
                               is_patient=False)
