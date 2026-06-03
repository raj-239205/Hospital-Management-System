from flask import Blueprint, render_template, request, redirect, url_for, flash
from .auth import login_required, role_required
from models import db, Medicine

pharmacy_bp = Blueprint('pharmacy', __name__)

@pharmacy_bp.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    status_filter = request.args.get('status', '').strip() # 'low' to show low stock
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Medicine.query
    
    if search_query:
        query = query.filter(Medicine.name.like(f"%{search_query}%"))
        
    if category_filter:
        query = query.filter(Medicine.category == category_filter)
        
    if status_filter == 'low':
        query = query.filter(Medicine.stock <= Medicine.low_stock_threshold)
        
    pagination = query.order_by(Medicine.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    medicines = pagination.items
    
    # Distinct categories for filter
    categories = [m.category for m in db.session.query(Medicine.category).distinct().all()]
    
    return render_template('pharmacy/list.html', medicines=medicines, pagination=pagination, search_query=search_query, category_filter=category_filter, status_filter=status_filter, categories=categories)

@pharmacy_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')  # Admin only to add new medicine definitions
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        stock = request.form.get('stock')
        price = request.form.get('price')
        threshold = request.form.get('low_stock_threshold', '10')
        
        if not name or not category or not stock or not price:
            flash('All fields are required.', 'danger')
            return render_template('pharmacy/form.html', action='Add', medicine=None)
            
        # Check uniqueness
        if Medicine.query.filter_by(name=name).first():
            flash('Medicine with this name already exists.', 'danger')
            return render_template('pharmacy/form.html', action='Add', medicine=None)
            
        try:
            stock_val = int(stock)
            price_val = float(price)
            threshold_val = int(threshold)
            if stock_val < 0 or price_val < 0 or threshold_val < 0:
                raise ValueError("Must be non-negative.")
        except ValueError:
            flash('Please enter valid positive numbers for stock, price, and threshold.', 'danger')
            return render_template('pharmacy/form.html', action='Add', medicine=None)
            
        medicine = Medicine(
            name=name, category=category, stock=stock_val,
            price=price_val, low_stock_threshold=threshold_val
        )
        db.session.add(medicine)
        db.session.commit()
        flash('Medicine added to inventory successfully!', 'success')
        return redirect(url_for('pharmacy.index'))
        
    return render_template('pharmacy/form.html', action='Add', medicine=None)

@pharmacy_bp.route('/edit/<int:medicine_id>', methods=['GET', 'POST'])
@login_required
def edit(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        stock = request.form.get('stock')
        price = request.form.get('price')
        threshold = request.form.get('low_stock_threshold')
        
        if not name or not category or not stock or not price:
            flash('All fields are required.', 'danger')
            return render_template('pharmacy/form.html', action='Edit', medicine=medicine)
            
        # Check uniqueness conflict
        existing = Medicine.query.filter_by(name=name).first()
        if existing and existing.id != medicine.id:
            flash('Another medicine with this name already exists.', 'danger')
            return render_template('pharmacy/form.html', action='Edit', medicine=medicine)
            
        try:
            medicine.stock = int(stock)
            medicine.price = float(price)
            medicine.low_stock_threshold = int(threshold)
        except ValueError:
            flash('Please enter valid numbers.', 'danger')
            return render_template('pharmacy/form.html', action='Edit', medicine=medicine)
            
        medicine.name = name
        medicine.category = category
        db.session.commit()
        flash('Medicine details updated successfully.', 'success')
        return redirect(url_for('pharmacy.index'))
        
    return render_template('pharmacy/form.html', action='Edit', medicine=medicine)

@pharmacy_bp.route('/update-stock/<int:medicine_id>', methods=['POST'])
@login_required
def update_stock(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    new_stock_str = request.form.get('stock')
    
    try:
        new_stock = int(new_stock_str)
        if new_stock < 0:
            raise ValueError()
        medicine.stock = new_stock
        db.session.commit()
        flash(f"Stock for {medicine.name} updated to {new_stock}.", 'success')
    except ValueError:
        flash('Invalid stock value. Must be a positive integer.', 'danger')
        
    return redirect(url_for('pharmacy.index'))

@pharmacy_bp.route('/delete/<int:medicine_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    db.session.delete(medicine)
    db.session.commit()
    flash('Medicine deleted from inventory.', 'success')
    return redirect(url_for('pharmacy.index'))
