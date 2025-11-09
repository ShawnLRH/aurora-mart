from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Customer
from django.contrib.auth import login
from .forms import SignUpForm
import csv
import os
from django.conf import settings
from decimal import Decimal

def home(request):
    products = Product.objects.all()
    featured_products = products[:4]
    popular_products = products[4:8]
    context = {
        'featured_products': featured_products,
        'popular_products': popular_products,
    }
    return render(request, 'ecommerce/home.html', context)

def product_detail(request, sku):
    product = get_object_or_404(Product, sku_code=sku)
    related_products = Product.objects.filter(product_category=product.product_category).exclude(id=product.id)[:4]
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'ecommerce/product.html', context)

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'ecommerce/signup.html', {'form': form})

def load_data(request):
    """
    Simple view to load all CSV data when accessed via GET request.
    Visit /loaddata to import all customer and product data.
    """
    def safe_read_csv(file_path):
        """Safely read CSV file with proper encoding handling"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # Replace problematic characters
                    content = content.replace('?', '-')
                    return csv.reader(content.splitlines())
            except UnicodeDecodeError:
                continue
        
        # Final fallback - read as binary and decode with error handling
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='replace')
            content = content.replace('?', '-').replace('\ufffd', '-')
            return csv.reader(content.splitlines())
    
    try:
        # Get the base directory of the project
        base_dir = settings.BASE_DIR
        
        # Import customers
        customers_imported = 0
        customers_file = os.path.join(base_dir, 'data', 'b2c_customers_100.csv')
        
        if os.path.exists(customers_file):
            csv_reader = safe_read_csv(customers_file)
            for row in csv_reader:
                if len(row) >= 10:  # Ensure we have at least the required fields
                    try:
                        # CSV columns: id,age,gender,employment_status,occupation,education,household_size,has_children,monthly_income_sgd,preferred_category
                        customer, created = Customer.objects.get_or_create(
                            age=int(row[1]),
                            gender=row[2].strip(),
                            employment_status=row[3].strip(),
                            occupation=row[4].strip(),
                            education=row[5].strip(),
                            household_size=int(row[6]),
                            has_children=bool(int(row[7])),
                            monthly_income_sgd=Decimal(str(row[8]).strip()),
                            preferred_category=row[9].strip()
                        )
                        if created:
                            customers_imported += 1
                    except (ValueError, IndexError) as e:
                        continue  # Skip invalid rows
        
        # Import products
        products_imported = 0
        products_file = os.path.join(base_dir, 'data', 'b2c_products_500.csv')
        
        if os.path.exists(products_file):
            csv_reader = safe_read_csv(products_file)
            for row in csv_reader:
                if len(row) >= 10:  # Ensure we have at least the required fields
                    try:
                        # CSV columns: id,sku_code,product_name,product_description,product_category,product_subcategory,quantity_on_hand,reorder_quantity,unit_price,product_rating
                        product, created = Product.objects.get_or_create(
                            sku_code=row[1].strip(),
                            defaults={
                                'product_name': row[2].strip(),
                                'product_description': row[3].strip(),
                                'product_category': row[4].strip(),
                                'product_subcategory': row[5].strip(),
                                'quantity_on_hand': int(row[6]),
                                'reorder_quantity': int(row[7]),
                                'unit_price': Decimal(str(row[8]).strip()),
                                'product_rating': Decimal(str(row[9]).strip())
                            }
                        )
                        if created:
                            products_imported += 1
                    except (ValueError, IndexError) as e:
                        continue  # Skip invalid rows
        
        # Return a simple success page
        from django.http import HttpResponse
        return HttpResponse(f"""
        <html>
        <head><title>Data Loaded Successfully</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h1 style="color: green;">✅ Data Import Complete!</h1>
            <p><strong>Customers imported:</strong> {customers_imported}</p>
            <p><strong>Products imported:</strong> {products_imported}</p>
            <p><strong>Total customers in database:</strong> {Customer.objects.count()}</p>
            <p><strong>Total products in database:</strong> {Product.objects.count()}</p>
            <hr>
            <p><a href="/">← Back to Home</a></p>
        </body>
        </html>
        """)
        
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"""
        <html>
        <head><title>Data Import Error</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h1 style="color: red;">❌ Import Failed</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><a href="/">← Back to Home</a></p>
        </body>
        </html>
        """)