# Hope Care - Hospital Management System

A production-ready, feature-rich **Hospital Management System (HMS)** web application built using Python Flask, SQLite, Bootstrap 5, and JavaScript. This project is structured following Object-Oriented Programming (OOP) principles, utilizes Flask Blueprints, and is powered by SQLAlchemy ORM.

---

## Project Overview

Hope Care is designed to streamline clinical workflows, patient management, doctor assignments, and pharmacy operations. The interface uses a sleek, custom-designed dark/light Clinical Teal and Deep Indigo corporate theme designed to feel premium and professional.

---

## Key Features

### 1. Secure Authentication & RBAC
- Role-Based Access Control (Admin vs. Doctor roles).
- Session-based navigation protection.
- Secure password hashing using `werkzeug.security`.

### 2. Comprehensive Dashboards
- **Admin View**: Displays analytics for total patients, doctors, scheduling metrics, and revenue. Includes interactive trend charts using **Chart.js**.
- **Doctor View**: Personalized scheduling dashboard showing assigned consultations and patients.

### 3. Patient & Doctor Management (CRUD)
- Patient admissions profile tracking, including demographics, diseases, and blood groups.
- Detailed medical and billing histories mapped directly on the patient profile.
- Doctor registries with contact info, availability, and automatic login credential setup.

### 4. Appointment Scheduler
- Interactive consultation booking form.
- Dynamic doctor dropdown population based on the selected clinical specialization (via async REST API).
- Status workflow tracking (Scheduled -> Completed / Cancelled).

### 5. Automated Billing & Invoicing
- Itemized billing (consultation fees, room board, pharmacy/medications).
- Auto-calculated GST rates and grand totals.
- Digital printable receipts (with window-print styling) and automatic **PDF invoice generation** using **ReportLab**.

### 6. Pharmacy Stock Inventory
- Real-time stock counts and threshold monitoring.
- Interactive inline stock adjustments.
- System-wide **Low Stock Alerts** with pulse animations.

### 7. Room & Ward Allocation
- Interactive room grid showing vacancy/occupancy.
- Support for room classifications (General, Semi-Private, Private, ICU, Emergency Room).
- Direct patient allocation and release.

### 8. Interactive Reports & Data Audits
- Administrative dashboard aggregating metrics.
- One-click exports to **PDF** (using ReportLab) and **Excel** sheets (using OpenPyXL) for Patient, Doctor, Appointment, and Revenue reports.

---

## Technologies Used

- **Back-End**: Python, Flask, Flask-SQLAlchemy (SQLite)
- **Front-End**: HTML5, Vanilla CSS3 (Custom clinical UI theme), Bootstrap 5, JavaScript (ES6)
- **Chart Visualizations**: Chart.js (CDN)
- **Libraries**: ReportLab (PDF processing), OpenPyXL (Excel generation)

---

## Installation & Setup

Follow these steps to run the application locally:

### 1. Clone the repository
```bash
git clone https://github.com/your-username/hospital-management-system.git
cd hospital-management-system
```

### 2. Install dependencies
Ensure Python is installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Seed the Database
Run the seeder script to recreate database tables, seed sample doctors, patients, billing registers, and configure default user profiles.
```bash
python seed.py
```
This configures the default portal login accounts:
* **Admin Login**: Username: `admin` | Password: `admin123`
* **Doctor Login**: Username: `house` | Password: `doctor123`

### 4. Run the Application
Start the Flask development server:
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000/`.

---

## Future Enhancements

- **Direct Email Notifications**: Integrate SMTP relays to email invoices directly to patients.
- **Doctor Consultation Notes**: Text editor inside the patient profile for doctors to log treatment notes.
- **REST API Security**: Secure REST endpoints using JWT keys.


It is available on 2 platforms
1.) Pythoneverywhere and access link for live demo is http://rajveer239.pythonanywhere.com/ 
2.) Render and access link is  https://hospital-management-system-7plv.onrender.com


It is not poosible in github because for github it is not possible to run at github deployment for any Python Flask application.

Here is why:

GitHub Pages is a static host: It acts like a folder of files. It can only serve files that the browser can run directly (like HTML, CSS, and basic JavaScript).
Flask requires a Python Server: Flask needs an active backend server to run the Python code, process routing requests (like logging in, routing to dashboards), and read/write to the SQLite database. GitHub Pages does not run any servers.
To have a live, working website with logins and databases, you must use a Python hosting service like Render or PythonAnywhere, which will automatically deploy your code from GitHub.
