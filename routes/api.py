from flask import Blueprint, jsonify, session
from .auth import login_required
from models import db, Patient, Doctor, Appointment, Bill, Medicine
from sqlalchemy import func
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/dashboard/charts')
@login_required
def chart_data():
    # 1. Appointment status breakdown
    appt_status_counts = db.session.query(
        Appointment.status, func.count(Appointment.id)
    ).group_by(Appointment.status).all()
    
    appt_labels = [row[0] for row in appt_status_counts]
    appt_values = [row[1] for row in appt_status_counts]
    
    # If empty, provide placeholder labels
    if not appt_labels:
        appt_labels = ['Scheduled', 'Completed', 'Cancelled']
        appt_values = [0, 0, 0]
        
    # 2. Revenue monthly trends (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_revenue = db.session.query(
        func.strftime('%Y-%m', Bill.date_generated).label('month'),
        func.sum(Bill.total_amount).label('total')
    ).filter(Bill.date_generated >= six_months_ago)\
     .group_by('month')\
     .order_by('month').all()
     
    revenue_labels = [row.month for row in monthly_revenue]
    revenue_values = [float(row.total) for row in monthly_revenue]
    
    # 3. Patient Blood Group distribution
    blood_distribution = db.session.query(
        Patient.blood_group, func.count(Patient.id)
    ).group_by(Patient.blood_group).all()
    
    blood_labels = [row[0] if row[0] else 'Unknown' for row in blood_distribution]
    blood_values = [row[1] for row in blood_distribution]
    
    return jsonify({
        'appointments': {
            'labels': appt_labels,
            'values': appt_values
        },
        'revenue': {
            'labels': revenue_labels,
            'values': revenue_values
        },
        'blood_groups': {
            'labels': blood_labels,
            'values': blood_values
        }
    })

@api_bp.route('/doctors/specialization/<string:spec>')
@login_required
def doctors_by_specialization(spec):
    doctors = Doctor.query.filter_by(specialization=spec, availability='Available').all()
    return jsonify([{'id': d.id, 'name': d.name} for d in doctors])

@api_bp.route('/pharmacy/low-stock')
@login_required
def low_stock_alerts():
    low_stock = Medicine.query.filter(Medicine.stock <= Medicine.low_stock_threshold).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'stock': m.stock,
        'threshold': m.low_stock_threshold
    } for m in low_stock])
