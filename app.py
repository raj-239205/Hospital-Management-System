import os
from flask import Flask, render_template, session, request, redirect, url_for, flash
from models import db, User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.patients import patients_bp
from routes.doctors import doctors_bp
from routes.appointments import appointments_bp
from routes.billing import billing_bp
from routes.pharmacy import pharmacy_bp
from routes.rooms import rooms_bp
from routes.reports import reports_bp
from routes.api import api_bp
from routes.prescriptions import prescriptions_bp

def create_app():
    app = Flask(__name__)
    
    # Configure application
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hope_hospital_super_secret_key_19283')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Profile Upload configs
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'profiles')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Initialize Database
    db.init_app(app)
    
    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp, url_prefix='/patients')
    app.register_blueprint(doctors_bp, url_prefix='/doctors')
    app.register_blueprint(appointments_bp, url_prefix='/appointments')
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(pharmacy_bp, url_prefix='/pharmacy')
    app.register_blueprint(rooms_bp, url_prefix='/rooms')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(prescriptions_bp, url_prefix='/prescriptions')
    app.register_blueprint(api_bp)
    
    # Template Context Processor
    @app.context_processor
    def inject_user_context():
        return {
            'current_user': {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'role': session.get('role'),
                'doctor_id': session.get('doctor_id'),
                'patient_id': session.get('patient_id'),
                'is_demo': session.get('is_demo', False)
            }
        }
        
    # Global Interceptor for Guest Demo Modifying Actions (POSTs)
    @app.before_request
    def check_demo_write_actions():
        if request.method == 'POST' and session.get('is_demo'):
            # Allow logout POST or special actions if any, otherwise block write actions
            if 'logout' not in request.path.lower() and 'login' not in request.path.lower():
                flash('Try Demo: Data modification is disabled. Please login to continue.', 'warning')
                return redirect(request.referrer or url_for('dashboard.index'))
                
    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
        
    # Database Initialization
    with app.app_context():
        db.create_all()
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
