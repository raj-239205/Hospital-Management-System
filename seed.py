from app import create_app
from models import db, User, Doctor, Patient, Appointment, Room, Medicine, Bill, Prescription, UserActivity
from datetime import datetime, date, timedelta
from routes.billing import generate_pdf

def seed_database():
    app = create_app()
    with app.app_context():
        # Clean up database
        db.drop_all()
        db.create_all()
        
        print("Database tables recreated successfully.")
        
        # 1. Add Rooms (Wards config)
        rooms = [
            Room(room_number="Ward-101A", room_type="General Ward", availability_status=True),
            Room(room_number="Ward-101B", room_type="General Ward", availability_status=True),
            Room(room_number="Semi-201", room_type="Semi-Private", availability_status=True),
            Room(room_number="Suite-301", room_type="Private Suite", availability_status=True),
            Room(room_number="ICU-401", room_type="ICU", availability_status=True),
            Room(room_number="ICU-402", room_type="ICU", availability_status=True),
            Room(room_number="ER-102", room_type="Emergency Room", availability_status=True),
        ]
        db.session.add_all(rooms)
        print("Rooms configured.")

        # 2. Add Medicines (Pharmacy)
        medicines = [
            Medicine(name="Paracetamol 500mg", category="Analgesics", stock=150, price=2.50, low_stock_threshold=20),
            Medicine(name="Amoxicillin 250mg", category="Antibiotics", stock=8, price=12.00, low_stock_threshold=15), # Low stock!
            Medicine(name="Ibuprofen 400mg", category="Analgesics", stock=85, price=4.20, low_stock_threshold=10),
            Medicine(name="Atorvastatin 20mg", category="Cardiovascular", stock=5, price=25.50, low_stock_threshold=12), # Low stock!
            Medicine(name="Metformin 500mg", category="Gastrointestinal", stock=120, price=8.80, low_stock_threshold=15),
            Medicine(name="Albuterol Inhaler", category="Other", stock=14, price=35.00, low_stock_threshold=5),
            Medicine(name="Vitamin C 1000mg", category="Vitamins & Supplements", stock=3, price=6.00, low_stock_threshold=10), # Low stock!
            Medicine(name="Lidocaine Injection", category="Anesthetics", stock=45, price=18.50, low_stock_threshold=10),
        ]
        db.session.add_all(medicines)
        print("Pharmacy stocks initialized.")

        # 3. Add Doctors (10 Doctors)
        doctors = [
            Doctor(name="Amit Sharma", specialization="Cardiology", phone="+91 98765 43210", email="doctor@hospitaldemo.com", experience=15, availability="Available"),
            Doctor(name="Priya Kapoor", specialization="Neurology", phone="+91 98765 43211", email="cameron@hopehospital.com", experience=12, availability="Available"),
            Doctor(name="Rohan Mehta", specialization="Orthopedic", phone="+91 98765 43212", email="foreman@hopehospital.com", experience=10, availability="Available"),
            Doctor(name="Neha Verma", specialization="Dermatologist", phone="+91 98765 43213", email="chase@hopehospital.com", experience=8, availability="Available"),
            Doctor(name="Vivek Gupta", specialization="Pediatrician", phone="+91 98765 43214", email="wilson@hopehospital.com", experience=11, availability="Available"),
            Doctor(name="Simran Kaur", specialization="Gynecologist", phone="+91 98765 43215", email="simran@hopehospital.com", experience=9, availability="Available"),
            Doctor(name="Rahul Yadav", specialization="General Medicine", phone="+91 98765 43216", email="rahul@hopehospital.com", experience=14, availability="Available"),
            Doctor(name="Arjun Malhotra", specialization="Oncology", phone="+91 98765 43217", email="arjun@hopehospital.com", experience=16, availability="Unavailable"), # On Leave
            Doctor(name="Karan Johar", specialization="Anesthesiology", phone="+91 98765 43218", email="karan@hopehospital.com", experience=7, availability="Available"),
            Doctor(name="Meera Sen", specialization="Ophthalmology", phone="+91 98765 43219", email="meera@hopehospital.com", experience=13, availability="Available"),
        ]
        db.session.add_all(doctors)
        db.session.flush() # Flush to get doctor.id values
        print("Doctors registered.")

        # 4. Add User Logins (Admin & Doctor accounts matching recruiter specs)
        admin = User(username="admin", email="admin@hospitaldemo.com", role="admin", is_verified=True)
        admin.set_password("Admin@123")
        db.session.add(admin)
        
        # Add Doctor log-in users linked to doctors (dramit -> Doctor@123)
        doc_users = [
            ("dramit", "Doctor@123", doctors[0].id),
            ("drpriya", "Doctor@123", doctors[1].id),
            ("drrohan", "Doctor@123", doctors[2].id),
            ("drneha", "Doctor@123", doctors[3].id),
        ]
        for username, pwd, doc_id in doc_users:
            u = User(username=username, email=doctors[doc_id-1].email, role="doctor", doctor_id=doc_id, is_verified=True)
            u.set_password(pwd)
            db.session.add(u)
        print("System portal user accounts configured.")

        # 5. Add Patients (20 Patients)
        today = date.today()
        patients = [
            Patient(name="Rajveer Choudhary", age=32, gender="Male", phone_number="+91 99999 11111", address="12 Ring Road, Delhi", blood_group="O+", disease="Typhoid", admission_date=today - timedelta(days=5), status="Admitted"),
            Patient(name="Aarav Sharma", age=45, gender="Male", phone_number="+91 99999 22222", address="45 Park Street, Mumbai", blood_group="A+", disease="Cardiac Checkup", admission_date=today - timedelta(days=2), status="Outpatient"),
            Patient(name="Priya Verma", age=28, gender="Female", phone_number="+91 99999 33333", address="89 Mall Road, Shimla", blood_group="B+", disease="Migraine", admission_date=today - timedelta(days=12), status="Admitted"),
            Patient(name="Rohit Singh", age=50, gender="Male", phone_number="+91 99999 44444", address="123 Sector-15, Chandigarh", blood_group="AB+", disease="Fractured Leg", admission_date=today - timedelta(days=1), status="Admitted"),
            Patient(name="Ananya Gupta", age=24, gender="Female", phone_number="+91 99999 55555", address="78 Salt Lake, Kolkata", blood_group="O-", disease="Dehydration", admission_date=today - timedelta(days=8), status="Discharged"),
            
            Patient(name="Aditya Mehta", age=62, gender="Male", phone_number="+91 99999 66666", address="4 C.G. Road, Ahmedabad", blood_group="A-", disease="Hypertension", admission_date=today - timedelta(days=15), status="Admitted"),
            Patient(name="Neha Joshi", age=35, gender="Female", phone_number="+91 99999 77777", address="56 FC Road, Pune", blood_group="B-", disease="Dermatitis", admission_date=today - timedelta(days=10), status="Outpatient"),
            Patient(name="Vivek Patel", age=41, gender="Male", phone_number="+91 99999 88888", address="90 Race Course, Vadodara", blood_group="O+", disease="Viral Fever", admission_date=today - timedelta(days=3), status="Admitted"),
            Patient(name="Simran Kaur", age=29, gender="Female", phone_number="+91 99999 99999", address="45 GT Road, Amritsar", blood_group="AB-", disease="Flu Checkup", admission_date=today - timedelta(days=6), status="Outpatient"),
            Patient(name="Rahul Yadav", age=38, gender="Male", phone_number="+91 99999 00000", address="12 Gomti Nagar, Lucknow", blood_group="B+", disease="Diabetes Control", admission_date=today - timedelta(days=20), status="Outpatient"),
            
            Patient(name="Kunal Kapoor", age=47, gender="Male", phone_number="+91 88888 11111", address="78 Juhu Scheme, Mumbai", blood_group="O+", disease="Kidney Stones", admission_date=today - timedelta(days=14), status="Admitted"),
            Patient(name="Diya Mirza", age=31, gender="Female", phone_number="+91 88888 22222", address="90 Banjara Hills, Hyderabad", blood_group="A+", disease="Thyroid Evaluation", admission_date=today - timedelta(days=4), status="Outpatient"),
            Patient(name="Vikram Rathore", age=55, gender="Male", phone_number="+91 88888 33333", address="12 Civil Lines, Jaipur", blood_group="B+", disease="Osteoarthritis", admission_date=today - timedelta(days=7), status="Admitted"),
            Patient(name="Sonia Gandhi", age=68, gender="Female", phone_number="+91 88888 44444", address="10 Janpath, New Delhi", blood_group="O-", disease="Bronchitis", admission_date=today - timedelta(days=11), status="Admitted"),
            Patient(name="Kabir Khan", age=36, gender="Male", phone_number="+91 88888 55555", address="34 Carter Road, Mumbai", blood_group="AB+", disease="Sprained Ankle", admission_date=today - timedelta(days=6), status="Discharged"),
            
            Patient(name="Ishaan Khattar", age=22, gender="Male", phone_number="+91 88888 66666", address="56 Linking Road, Mumbai", blood_group="B-", disease="Food Poisoning", admission_date=today - timedelta(days=3), status="Admitted"),
            Patient(name="Kiara Advani", age=29, gender="Female", phone_number="+91 88888 77777", address="12 Peddar Road, Mumbai", blood_group="A-", disease="Migraine", admission_date=today - timedelta(days=9), status="Outpatient"),
            Patient(name="Siddharth Malhotra", age=33, gender="Male", phone_number="+91 88888 88888", address="45 Defence Colony, Delhi", blood_group="O+", disease="Viral Tonsillitis", admission_date=today - timedelta(days=2), status="Admitted"),
            Patient(name="Alia Bhatt", age=30, gender="Female", phone_number="+91 88888 99999", address="89 Bandra West, Mumbai", blood_group="A+", disease="Pregnancy Checkup", admission_date=today - timedelta(days=5), status="Outpatient"),
            Patient(name="Ranbir Kapoor", age=42, gender="Male", phone_number="+91 88888 00000", address="89 Bandra West, Mumbai", blood_group="AB-", disease="Knee Ligament Tear", admission_date=today - timedelta(days=18), status="Admitted"),
        ]
        db.session.add_all(patients)
        db.session.flush()
        print("Patients database initialized.")

        # Create Patient portal login for Rajveer (rajveer -> Patient@123)
        patient_user = User(username="rajveer", email="patient@hospitaldemo.com", role="patient", patient_id=patients[0].id, is_verified=True)
        patient_user.set_password("Patient@123")
        db.session.add(patient_user)

        # 6. Assign Rooms to admitted patients
        rooms[4].assigned_patient_id = patients[0].id # Rajveer in ICU-401
        rooms[4].availability_status = False
        
        rooms[3].assigned_patient_id = patients[2].id # Priya Verma in Suite-301
        rooms[3].availability_status = False
        
        rooms[0].assigned_patient_id = patients[3].id # Rohit Singh in Ward-101A
        rooms[0].availability_status = False
        
        rooms[5].assigned_patient_id = patients[5].id # Aditya Mehta in ICU-402
        rooms[5].availability_status = False
        
        rooms[6].assigned_patient_id = patients[7].id # Vivek Patel in ER-102
        rooms[6].availability_status = False
        print("Rooms occupied.")

        # 7. Add Appointments (15 Appointments)
        appointments = [
            Appointment(patient_id=patients[0].id, doctor_id=doctors[0].id, appointment_date=today + timedelta(days=1), appointment_time="10:00 AM", status="Scheduled"),
            Appointment(patient_id=patients[1].id, doctor_id=doctors[3].id, appointment_date=today + timedelta(days=2), appointment_time="02:00 PM", status="Scheduled"),
            Appointment(patient_id=patients[2].id, doctor_id=doctors[0].id, appointment_date=today, appointment_time="11:30 AM", status="Scheduled"),
            Appointment(patient_id=patients[3].id, doctor_id=doctors[1].id, appointment_date=today + timedelta(days=3), appointment_time="04:00 PM", status="Scheduled"),
            Appointment(patient_id=patients[4].id, doctor_id=doctors[2].id, appointment_date=today - timedelta(days=8), appointment_time="09:00 AM", status="Completed"),
            
            # Additional appointments
            Appointment(patient_id=patients[5].id, doctor_id=doctors[0].id, appointment_date=today, appointment_time="09:30 AM", status="Scheduled"),
            Appointment(patient_id=patients[6].id, doctor_id=doctors[1].id, appointment_date=today - timedelta(days=5), appointment_time="11:00 AM", status="Completed"),
            Appointment(patient_id=patients[7].id, doctor_id=doctors[2].id, appointment_date=today + timedelta(days=4), appointment_time="10:30 AM", status="Scheduled"),
            Appointment(patient_id=patients[8].id, doctor_id=doctors[3].id, appointment_date=today + timedelta(days=1), appointment_time="03:30 PM", status="Scheduled"),
            Appointment(patient_id=patients[9].id, doctor_id=doctors[0].id, appointment_date=today - timedelta(days=12), appointment_time="02:00 PM", status="Completed"),
            
            Appointment(patient_id=patients[10].id, doctor_id=doctors[4].id, appointment_date=today - timedelta(days=1), appointment_time="10:00 AM", status="Cancelled"),
            Appointment(patient_id=patients[11].id, doctor_id=doctors[2].id, appointment_date=today - timedelta(days=15), appointment_time="01:30 PM", status="Completed"),
            Appointment(patient_id=patients[12].id, doctor_id=doctors[0].id, appointment_date=today - timedelta(days=20), appointment_time="09:00 AM", status="Completed"),
            Appointment(patient_id=patients[13].id, doctor_id=doctors[3].id, appointment_date=today + timedelta(days=5), appointment_time="11:00 AM", status="Scheduled"),
            Appointment(patient_id=patients[14].id, doctor_id=doctors[2].id, appointment_date=today + timedelta(days=7), appointment_time="04:00 PM", status="Scheduled"),
        ]
        db.session.add_all(appointments)
        print("Schedules populated.")

        # 8. Add Invoices/Bills and generate PDF files
        bills = [
            Bill(patient_id=patients[4].id, consultation_charges=120.0, medicine_charges=48.50, room_charges=350.0, gst_rate=18.0, total_amount=round((120.0 + 48.50 + 350.0) * 1.18, 2), date_generated=datetime.now() - timedelta(days=8)),
            Bill(patient_id=patients[2].id, consultation_charges=150.0, medicine_charges=124.0, room_charges=1200.0, gst_rate=18.0, total_amount=round((150.0 + 124.0 + 1200.0) * 1.18, 2), date_generated=datetime.now() - timedelta(days=2)),
            Bill(patient_id=patients[0].id, consultation_charges=200.0, medicine_charges=250.0, room_charges=800.0, gst_rate=18.0, total_amount=round((200.0 + 250.0 + 800.0) * 1.18, 2), date_generated=datetime.now() - timedelta(days=1)),
            Bill(patient_id=patients[9].id, consultation_charges=80.0, medicine_charges=15.0, room_charges=0.0, gst_rate=18.0, total_amount=round((80.0 + 15.0 + 0.0) * 1.18, 2), date_generated=datetime.now() - timedelta(days=12)),
        ]
        db.session.add_all(bills)
        db.session.flush() # Flush to get bill IDs
        
        # Generate the physical PDFs for these seeded bills
        for bill in bills:
            pdf_filename = generate_pdf(bill)
            bill.invoice_pdf_path = pdf_filename
        print("Invoices generated.")

        # 9. Add Prescriptions
        prescriptions = [
            Prescription(patient_id=patients[0].id, doctor_id=doctors[0].id, date_written=today - timedelta(days=4), symptoms="Fever, chills, headache", diagnosis="Severe Typhoid", medications="Ciprofloxacin 500mg - Twice daily for 10 days.\nParacetamol 500mg - as needed for high fever.", instructions="Complete bed rest. Drink boiled water. Avoid spicy foods."),
            Prescription(patient_id=patients[2].id, doctor_id=doctors[1].id, date_written=today - timedelta(days=2), symptoms="Frequent severe headaches, sensory aura", diagnosis="Chronic Migraine", medications="Sumatriptan 50mg - At onset of headache.\nPropranolol 40mg - Once daily for prevention.", instructions="Avoid caffeine triggers. Sleep in dark room during attacks. Monitor symptoms."),
            Prescription(patient_id=patients[5].id, doctor_id=doctors[0].id, date_written=today - timedelta(days=1), symptoms="Shortness of breath, chest pressure", diagnosis="Coronary Artery Checks", medications="Aspirin 75mg - Once daily in morning.\nAtorvastatin 20mg - Once daily at night.", instructions="Avoid strenuous activity. Low salt diet. Follow up in cardiology OPD."),
        ]
        db.session.add_all(prescriptions)
        print("Prescriptions written.")

        # 10. Add User Activity Audit Logs
        activities = [
            UserActivity(user_id=1, username="admin", action="System Seeding", details="Initial database config complete"),
            UserActivity(user_id=1, username="admin", action="Configure Rooms", details="Added ER-102 and ICU-402 configurations"),
            UserActivity(user_id=2, username="dramit", action="Write Prescription", details="Wrote RX-001 for Rajveer Choudhary"),
            UserActivity(user_id=1, username="admin", action="Create Doctor", details="Created portal logins for Dr. Rohan Mehta"),
        ]
        db.session.add_all(activities)
        
        db.session.commit()
        print("Invoices, Prescriptions, and Audit Trail logs generated.")
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    seed_database()
