import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from .auth import login_required, role_required
from models import db, Bill, Patient, Room
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime

billing_bp = Blueprint('billing', __name__)

def generate_pdf(bill):
    # Ensure the reports folder exists
    reports_dir = os.path.join(current_app.root_path, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    filename = f"invoice_{bill.id}.pdf"
    filepath = os.path.join(reports_dir, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#008080'), # Teal theme
        spaceAfter=15
    )
    
    header_style = ParagraphStyle(
        'InvoiceHeader',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4A4A4A')
    )
    
    subheader_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10
    )
    
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=12
    )
    
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white,
        leading=12
    )
    
    story = []
    
    # Title / Banner
    story.append(Paragraph("HOPE GENERAL HOSPITAL", title_style))
    story.append(Paragraph("123 Healthcare Boulevard, Medical District<br/>Phone: +1 (555) 019-2834 | Email: contact@hopehospital.com", header_style))
    story.append(Spacer(1, 20))
    
    # Divider Line
    d_table = Table([[""]], colWidths=[530])
    d_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor('#008080')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(d_table)
    story.append(Spacer(1, 15))
    
    # Patient Info & Invoice Metadata
    invoice_date = bill.date_generated.strftime('%Y-%m-%d %H:%M')
    info_data = [
        [
            Paragraph(f"<b>PATIENT DETAILS:</b><br/>ID: P{bill.patient.id}<br/>Name: {bill.patient.name}<br/>Age: {bill.patient.age} | Gender: {bill.patient.gender}<br/>Phone: {bill.patient.phone_number}", header_style),
            Paragraph(f"<b>INVOICE DETAILS:</b><br/>Invoice No: #INV-{bill.id:05d}<br/>Date: {invoice_date}<br/>Status: Paid", header_style)
        ]
    ]
    info_table = Table(info_data, colWidths=[265, 265])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 25))
    
    # Itemized Table
    subtotal = bill.consultation_charges + bill.medicine_charges + bill.room_charges
    gst_amt = (bill.gst_rate / 100) * subtotal
    
    table_data = [
        [Paragraph("Description", table_header), Paragraph("Amount ($)", table_header)],
        [Paragraph("Consultation & Professional Doctor Fees", table_text), Paragraph(f"${bill.consultation_charges:.2f}", table_text)],
        [Paragraph("Pharmacy & Medication Charges", table_text), Paragraph(f"${bill.medicine_charges:.2f}", table_text)],
        [Paragraph("Room & Ward Allocation Charges", table_text), Paragraph(f"${bill.room_charges:.2f}", table_text)],
        [Paragraph("<b>Subtotal</b>", table_text), Paragraph(f"${subtotal:.2f}", table_text)],
        [Paragraph(f"<b>GST ({bill.gst_rate}%)</b>", table_text), Paragraph(f"${gst_amt:.2f}", table_text)],
        [Paragraph("<b>Grand Total (USD)</b>", table_text), Paragraph(f"<b>${bill.total_amount:.2f}</b>", table_text)]
    ]
    
    item_table = Table(table_data, colWidths=[400, 130])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#008080')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (1, 3), 0.5, colors.HexColor('#E0E0E0')),
        ('BACKGROUND', (0, 4), (1, 6), colors.HexColor('#F5F5F5')),
        ('LINEABOVE', (0, 4), (1, 4), 1.5, colors.HexColor('#008080')),
        ('LINEABOVE', (0, 6), (1, 6), 1.5, colors.HexColor('#008080')),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 40))
    
    # Signature / Footer
    footer_data = [
        [
            Paragraph("Authorized Signature: _______________________", header_style),
            Paragraph("Thank you for choosing Hope Hospital.", ParagraphStyle('RightText', parent=header_style, alignment=2))
        ]
    ]
    footer_table = Table(footer_data, colWidths=[265, 265])
    story.append(footer_table)
    
    doc.build(story)
    
    return filename

@billing_bp.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Bill.query
    
    if search_query:
        query = query.join(Patient).filter(Patient.name.like(f"%{search_query}%"))
        
    pagination = query.order_by(Bill.date_generated.desc()).paginate(page=page, per_page=per_page, error_out=False)
    bills = pagination.items
    
    return render_template('billing/list.html', bills=bills, pagination=pagination, search_query=search_query)

@billing_bp.route('/generate', methods=['GET', 'POST'])
@login_required
@role_required('admin')  # Only admin can generate bills
def generate():
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        consultation = request.form.get('consultation_charges')
        medicine = request.form.get('medicine_charges')
        room_charges_val = request.form.get('room_charges')
        gst_rate_val = request.form.get('gst_rate', '18')
        
        if not patient_id:
            flash('Please select a patient.', 'danger')
            return redirect(url_for('billing.generate'))
            
        try:
            consultation = float(consultation) if consultation else 0.0
            medicine = float(medicine) if medicine else 0.0
            room_charges = float(room_charges_val) if room_charges_val else 0.0
            gst_rate = float(gst_rate_val) if gst_rate_val else 18.0
        except ValueError:
            flash('Charges and GST must be numerical values.', 'danger')
            return redirect(url_for('billing.generate'))
            
        subtotal = consultation + medicine + room_charges
        total = subtotal + (subtotal * (gst_rate / 100.0))
        
        bill = Bill(
            patient_id=patient_id,
            consultation_charges=consultation,
            medicine_charges=medicine,
            room_charges=room_charges,
            gst_rate=gst_rate,
            total_amount=round(total, 2)
        )
        
        db.session.add(bill)
        db.session.flush() # Flush to get bill.id for PDF name
        
        # Generate the PDF file
        pdf_filename = generate_pdf(bill)
        bill.invoice_pdf_path = pdf_filename
        
        db.session.commit()
        flash('Bill and PDF invoice generated successfully!', 'success')
        return redirect(url_for('billing.view', bill_id=bill.id))
        
    patients = Patient.query.all()
    rooms = Room.query.filter_by(availability_status=False).all() # Occupied rooms to calculate ward fees easily if needed
    
    # Pre-select patient if ID is passed
    pre_selected_patient_id = request.args.get('patient_id', type=int)
    
    return render_template('billing/generate.html', patients=patients, rooms=rooms, pre_selected_patient_id=pre_selected_patient_id)

@billing_bp.route('/view/<int:bill_id>')
@login_required
def view(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    subtotal = bill.consultation_charges + bill.medicine_charges + bill.room_charges
    gst_amt = subtotal * (bill.gst_rate / 100.0)
    
    return render_template('billing/invoice.html', bill=bill, subtotal=subtotal, gst_amt=gst_amt)

@billing_bp.route('/download/<int:bill_id>')
@login_required
def download(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    
    # Ensure PDF exists. If not, generate it
    reports_dir = os.path.join(current_app.root_path, 'reports')
    filepath = os.path.join(reports_dir, bill.invoice_pdf_path) if bill.invoice_pdf_path else None
    
    if not filepath or not os.path.exists(filepath):
        pdf_filename = generate_pdf(bill)
        bill.invoice_pdf_path = pdf_filename
        db.session.commit()
        filepath = os.path.join(reports_dir, pdf_filename)
        
    return send_file(filepath, as_attachment=True, download_name=f"invoice_{bill.id}.pdf")
