from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from .auth import login_required, role_required
from models import db, Prescription, Patient, Doctor

prescriptions_bp = Blueprint('prescriptions', __name__)

@prescriptions_bp.route('/')
@login_required
def index():
    role = session.get('role')
    user_id = session.get('user_id')
    patient_id = session.get('patient_id')
    doctor_id = session.get('doctor_id')
    
    if role == 'patient':
        # Patients only see their own prescriptions
        prescriptions = Prescription.query.filter_by(patient_id=patient_id).order_by(Prescription.date_written.desc()).all()
    elif role == 'doctor':
        # Doctors see prescriptions they wrote
        prescriptions = Prescription.query.filter_by(doctor_id=doctor_id).order_by(Prescription.date_written.desc()).all()
    else:
        # Admins see all
        prescriptions = Prescription.query.order_by(Prescription.date_written.desc()).all()
        
    return render_template('prescriptions/list.html', prescriptions=prescriptions)

@prescriptions_bp.route('/write', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'doctor'])
def write():
    if request.method == 'POST':
        # Demo write check
        if session.get('is_demo'):
            flash('Try Demo: Data modification is disabled. Please login to continue.', 'warning')
            return redirect(url_for('prescriptions.index'))
            
        patient_id = request.form.get('patient_id')
        symptoms = request.form.get('symptoms')
        diagnosis = request.form.get('diagnosis')
        medications = request.form.get('medications')
        instructions = request.form.get('instructions')
        
        # Doctor ID resolution
        if session.get('role') == 'doctor':
            doc_id = session.get('doctor_id')
        else:
            doc_id = request.form.get('doctor_id')
            
        if not patient_id or not medications or not doc_id:
            flash('Patient, Doctor, and Medications list are required fields.', 'danger')
            return redirect(url_for('prescriptions.write'))
            
        prescription = Prescription(
            patient_id=patient_id,
            doctor_id=doc_id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            medications=medications,
            instructions=instructions,
            date_written=datetime.utcnow().date()
        )
        db.session.add(prescription)
        db.session.commit()
        flash('Prescription written successfully!', 'success')
        return redirect(url_for('prescriptions.index'))
        
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    return render_template('prescriptions/form.html', patients=patients, doctors=doctors)

@prescriptions_bp.route('/view/<int:prescription_id>')
@login_required
def view(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    
    # Access checks
    role = session.get('role')
    if role == 'patient' and prescription.patient_id != session.get('patient_id'):
        flash('Access denied.', 'danger')
        return redirect(url_for('prescriptions.index'))
    elif role == 'doctor' and prescription.doctor_id != session.get('doctor_id'):
        flash('Access denied.', 'danger')
        return redirect(url_for('prescriptions.index'))
        
    return render_template('prescriptions/view.html', prescription=prescription)

@prescriptions_bp.route('/delete/<int:prescription_id>', methods=['POST'])
@login_required
@role_required(['admin', 'doctor'])
def delete(prescription_id):
    if session.get('is_demo'):
        flash('Try Demo: Data modification is disabled. Please login to continue.', 'warning')
        return redirect(url_for('prescriptions.index'))
        
    prescription = Prescription.query.get_or_404(prescription_id)
    
    if session.get('role') == 'doctor' and prescription.doctor_id != session.get('doctor_id'):
        flash('You can only delete prescriptions you wrote.', 'danger')
        return redirect(url_for('prescriptions.index'))
        
    db.session.delete(prescription)
    db.session.commit()
    flash('Prescription deleted successfully.', 'success')
    return redirect(url_for('prescriptions.index'))
