from flask import Blueprint, render_template, request, redirect, url_for, flash
from .auth import login_required, role_required
from models import db, Room, Patient

rooms_bp = Blueprint('rooms', __name__)

@rooms_bp.route('/')
@login_required
def index():
    rooms = Room.query.all()
    patients = Patient.query.filter(Patient.status == 'Admitted').all()
    
    # Check which patients already have rooms
    patients_with_rooms = [r.assigned_patient_id for r in rooms if r.assigned_patient_id]
    
    # Filter out patients who already have rooms assigned
    available_patients = [p for p in patients if p.id not in patients_with_rooms]
    
    return render_template('rooms/list.html', rooms=rooms, available_patients=available_patients)

@rooms_bp.route('/add', methods=['POST'])
@login_required
@role_required('admin')
def add():
    room_number = request.form.get('room_number')
    room_type = request.form.get('room_type')
    
    if not room_number or not room_type:
        flash('Room Number and Room Type are required.', 'danger')
        return redirect(url_for('rooms.index'))
        
    # Check if room already exists
    existing = Room.query.filter_by(room_number=room_number).first()
    if existing:
        flash(f"Room {room_number} already exists.", 'danger')
        return redirect(url_for('rooms.index'))
        
    room = Room(room_number=room_number, room_type=room_type, availability_status=True)
    db.session.add(room)
    db.session.commit()
    
    flash(f"Room {room_number} added successfully.", 'success')
    return redirect(url_for('rooms.index'))

@rooms_bp.route('/assign/<string:room_number>', methods=['POST'])
@login_required
def assign(room_number):
    room = Room.query.get_or_404(room_number)
    patient_id = request.form.get('patient_id')
    
    if not patient_id:
        flash('Please select a patient.', 'danger')
        return redirect(url_for('rooms.index'))
        
    patient = Patient.query.get(patient_id)
    if not patient:
        flash('Patient not found.', 'danger')
        return redirect(url_for('rooms.index'))
        
    # Check if patient already has a room
    already_assigned = Room.query.filter_by(assigned_patient_id=patient_id).first()
    if already_assigned:
        flash(f"Patient is already assigned to Room {already_assigned.room_number}.", 'warning')
        return redirect(url_for('rooms.index'))
        
    room.assigned_patient_id = patient_id
    room.availability_status = False
    db.session.commit()
    
    flash(f"Room {room_number} assigned to {patient.name} successfully.", 'success')
    return redirect(url_for('rooms.index'))

@rooms_bp.route('/release/<string:room_number>', methods=['POST'])
@login_required
def release(room_number):
    room = Room.query.get_or_404(room_number)
    
    if room.assigned_patient_id:
        patient_name = room.assigned_patient.name
        room.assigned_patient_id = None
        room.availability_status = True
        db.session.commit()
        flash(f"Room {room_number} released from patient {patient_name}.", 'success')
    else:
        flash('Room is already vacant.', 'warning')
        
    return redirect(url_for('rooms.index'))

@rooms_bp.route('/delete/<string:room_number>', methods=['POST'])
@login_required
@role_required('admin')
def delete(room_number):
    room = Room.query.get_or_404(room_number)
    
    if not room.availability_status:
        flash(f"Cannot delete Room {room_number} because it is currently occupied.", 'danger')
        return redirect(url_for('rooms.index'))
        
    db.session.delete(room)
    db.session.commit()
    
    flash(f"Room {room_number} deleted successfully.", 'success')
    return redirect(url_for('rooms.index'))
