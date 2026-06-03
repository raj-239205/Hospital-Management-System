import uuid
import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response, current_app
from functools import wraps
from werkzeug.utils import secure_filename
from models import db, User, Doctor, Patient, UserActivity
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def log_activity(user_id, username, action, details=None):
    try:
        activity = UserActivity(
            user_id=user_id if user_id and user_id != 9999 else None,
            username=username,
            action=action,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging activity: {e}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Check remember_me cookie
            remember_token = request.cookies.get('remember_token')
            if remember_token:
                user = User.query.filter_by(verification_token=remember_token).first()
                if user:
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['role'] = user.role
                    if user.doctor_id:
                        session['doctor_id'] = user.doctor_id
                    if user.patient_id:
                        session['patient_id'] = user.patient_id
                    return f(*args, **kwargs)
            
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    if isinstance(roles, str):
        roles = [roles]
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') not in roles:
                flash('Unauthorized access: You do not have permission to view this page.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        login_input = request.form.get('username')  # Form field still called 'username'
        password = request.form.get('password')
        role = request.form.get('role')
        remember = request.form.get('remember')
        
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()
        
        if user and user.check_password(password):
            if user.role != role:
                flash('Invalid role selected for this account.', 'danger')
                return render_template('auth/login.html')
                
            if not user.is_verified:
                flash(f'Please verify your email address first. [Simulated Link: /verify-email/{user.verification_token}]', 'warning')
                return render_template('auth/login.html')
                
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            if user.doctor_id:
                session['doctor_id'] = user.doctor_id
            if user.patient_id:
                session['patient_id'] = user.patient_id
                
            log_activity(user.id, user.username, 'Login', f"Logged in as {user.role}")
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            response = make_response(redirect(url_for('dashboard.index')))
            if remember:
                # Store a token for cookies
                token = str(uuid.uuid4())
                user.verification_token = token
                db.session.commit()
                response.set_cookie('remember_token', token, max_age=30*24*60*60) # 30 days
            return response
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        phone = request.form.get('phone_number')
        address = request.form.get('address')
        blood_group = request.form.get('blood_group')
        
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not name or not age or not gender or not phone or not address or not username or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'danger')
            return render_template('auth/register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email is already registered.', 'danger')
            return render_template('auth/register.html')
            
        try:
            # Create Patient Profile
            patient = Patient(
                name=name, age=int(age), gender=gender, phone_number=phone,
                address=address, blood_group=blood_group, status='Outpatient'
            )
            db.session.add(patient)
            db.session.flush()
            
            # Create User login
            token = str(uuid.uuid4())
            user = User(
                username=username, email=email, role='patient',
                patient_id=patient.id, is_verified=False, verification_token=token
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Log simulated verification email link
            print(f"\n[SIMULATED EMAIL SERVICE] Verify address {email} by clicking: http://127.0.0.1:5000/verify-email/{token}\n")
            flash(f'Registration successful! Please verify your email. [Simulated Link: /verify-email/{token}]', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error during registration: {e}", 'danger')
            
    return render_template('auth/register.html')

@auth_bp.route('/verify-email/<string:token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        log_activity(user.id, user.username, 'Email Verification', 'Successfully verified email address')
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('Invalid or expired email verification link.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = str(uuid.uuid4())
            user.verification_token = token
            db.session.commit()
            print(f"\n[SIMULATED EMAIL SERVICE] Reset password link: http://127.0.0.1:5000/reset-password/{token}\n")
            flash(f'Password reset link generated! [Simulated Link: /reset-password/{token}]', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('No account found with this email address.', 'danger')
            
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<string:token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        if password:
            user.set_password(password)
            user.verification_token = None
            db.session.commit()
            log_activity(user.id, user.username, 'Password Reset', 'Password was successfully reset')
            flash('Password reset successfully! Please login with your new credentials.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Please enter a valid password.', 'danger')
            
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/try-demo/<string:role>')
def try_demo(role):
    # Logs the user in as a guest role
    session.clear()
    session['user_id'] = 9999
    session['username'] = f"demo_{role}"
    session['role'] = role
    session['is_demo'] = True
    
    if role == 'doctor':
        # Assign to first doctor in the DB
        first_doc = Doctor.query.first()
        session['doctor_id'] = first_doc.id if first_doc else 1
    elif role == 'patient':
        # Assign to first patient in the DB
        first_pat = Patient.query.first()
        session['patient_id'] = first_pat.id if first_pat else 1
        
    flash(f"Logged in to Demo Mode as {role.upper()}. Data modification is disabled.", 'info')
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    
    # Audit log activities
    activities = UserActivity.query.filter_by(user_id=user.id).order_by(UserActivity.timestamp.desc()).limit(15).all() if user else []
    
    if request.method == 'POST':
        if session.get('is_demo'):
            flash('Try Demo: Profile updates are disabled in sandbox mode.', 'warning')
            return redirect(url_for('auth.profile'))
            
        action_type = request.form.get('action_type')
        
        # Profile Data Update
        if action_type == 'update_profile':
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            
            # Sub-records reference updates
            if user.role == 'doctor' and user.doctor:
                user.doctor.phone = phone
                user.doctor.email = email
            elif user.role == 'patient' and user.patient:
                user.patient.phone_number = phone
                user.patient.address = address
                
            user.email = email
            
            # Photo Upload
            photo_file = request.files.get('profile_photo')
            if photo_file and photo_file.filename:
                # Validate extension
                ext = os.path.splitext(photo_file.filename)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png']:
                    filename = f"user_{user.id}{ext}"
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    photo_file.save(filepath)
                    user.profile_photo = filename
                    
            db.session.commit()
            log_activity(user.id, user.username, 'Profile Update', 'Updated contact/avatar settings')
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        # Password Change Update
        elif action_type == 'change_password':
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            
            if user.check_password(old_password):
                user.set_password(new_password)
                db.session.commit()
                log_activity(user.id, user.username, 'Password Change', 'Modified login password')
                flash('Password changed successfully!', 'success')
                return redirect(url_for('auth.profile'))
            else:
                flash('Incorrect current password.', 'danger')
                return redirect(url_for('auth.profile'))
                
    return render_template('auth/profile.html', user=user, activities=activities)

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    username = session.get('username')
    if user_id and not session.get('is_demo'):
        log_activity(user_id, username, 'Logout', 'Logged out of system')
        
    session.clear()
    response = make_response(redirect(url_for('auth.login')))
    response.delete_cookie('remember_token')
    flash('Logged out successfully.', 'info')
    return response

@auth_bp.route('/about-project')
def about_project():
    return render_template('about.html')
