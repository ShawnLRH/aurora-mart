from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product, Customer, Cart, CartItem
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
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f'Welcome {user.first_name}! Your account has been created successfully.')
                return redirect('home')
            except Exception as e:
                messages.error(request, f'An error occurred while creating your account. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
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


def get_or_create_cart(user):
    """Helper function to get or create a cart for the user"""
    if user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=user)
        return cart
    return None


@login_required
def cart_view(request):
    """Display the user's shopping cart"""
    cart = get_or_create_cart(request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'ecommerce/cart.html', context)


@login_required
def add_to_cart(request, sku):
    """Add a product to the cart"""
    if request.method == 'POST':
        product = get_object_or_404(Product, sku_code=sku)
        cart = get_or_create_cart(request.user)
        
        quantity = int(request.POST.get('quantity', 1))
        
        # Check if product already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            cart_item.save()
        
        messages.success(request, f'{product.product_name} added to cart!')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{product.product_name} added to cart!',
                'cart_total': cart.total_items
            })
        
        return redirect('product_detail', sku=sku)
    
    return redirect('home')


@login_required
def update_cart_item(request, item_id):
    """Update quantity of a cart item"""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully!')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart!')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart = cart_item.cart if cart_item.pk else request.user.cart
            return JsonResponse({
                'success': True,
                'cart_total': cart.total_items,
                'subtotal': float(cart.subtotal),
                'item_total': float(cart_item.total_price) if cart_item.pk else 0
            })
    
    return redirect('cart_view')


@login_required
def remove_from_cart(request, item_id):
    """Remove an item from the cart"""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        product_name = cart_item.product.product_name
        cart_item.delete()
        messages.success(request, f'{product_name} removed from cart!')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart = request.user.cart
            return JsonResponse({
                'success': True,
                'message': f'{product_name} removed from cart!',
                'cart_total': cart.total_items,
                'subtotal': float(cart.subtotal)
            })
    
    return redirect('cart_view')


@login_required
def clear_cart(request):
    """Clear all items from the cart"""
    if request.method == 'POST':
        cart = get_or_create_cart(request.user)
        cart.items.all().delete()
        messages.success(request, 'Cart cleared!')
    
    return redirect('cart_view')