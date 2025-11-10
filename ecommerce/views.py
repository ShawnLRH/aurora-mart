from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Customer, Cart, CartItem
from django.contrib.auth import login
from .forms import SignUpForm
from .ai_utils import get_category_predictor, get_product_recommender
import csv
import os
from django.conf import settings
from decimal import Decimal

def home(request):
    # Personalize product recommendations based on user's preferred category
    if request.user.is_authenticated and hasattr(request.user, 'customer'):
        customer = request.user.customer
        if customer.preferred_category:
            # Show products from user's preferred category first
            featured_products = Product.objects.filter(
                product_category=customer.preferred_category
            ).order_by('-product_rating')[:4]
            
            print(f"🎯 Personalized home for {request.user.email}: {customer.preferred_category} ({featured_products.count()} products found)")
            
            # If not enough products in preferred category, fill with top-rated products
            if featured_products.count() < 4:
                remaining_count = 4 - featured_products.count()
                other_products = Product.objects.exclude(
                    product_category=customer.preferred_category
                ).order_by('-product_rating')[:remaining_count]
                featured_products = list(featured_products) + list(other_products)
                print(f"   Added {remaining_count} products from other categories")
        else:
            # Default: show top-rated products
            print(f"⚠️  User {request.user.email} has no preferred category, showing top-rated")
            featured_products = Product.objects.all().order_by('-product_rating')[:4]
    else:
        # For anonymous users, show top-rated products
        print(f"👤 Anonymous user, showing top-rated products")
        featured_products = Product.objects.all().order_by('-product_rating')[:4]
    
    # Popular products: best sellers (highest rated)
    popular_products = Product.objects.all().order_by('-product_rating')[4:8]
    
    # Get all categories for navigation
    all_categories = Product.objects.values_list('product_category', flat=True).distinct().order_by('product_category')
    
    context = {
        'featured_products': featured_products,
        'popular_products': popular_products,
        'all_categories': all_categories,
    }
    return render(request, 'ecommerce/home.html', context)

def product_detail(request, sku):
    product = get_object_or_404(Product, sku_code=sku)
    
    # Use AI to get "Frequently Bought Together" recommendations
    frequently_bought_together = []
    try:
        recommender = get_product_recommender()
        recommendations = recommender.get_frequently_bought_together(sku, top_n=4)
        
        # Fetch product objects for the recommendations
        for rec in recommendations:
            try:
                rec_product = Product.objects.get(sku_code=rec['sku'])
                frequently_bought_together.append({
                    'product': rec_product,
                    'confidence': rec['confidence'],
                    'lift': rec['lift']
                })
            except Product.DoesNotExist:
                continue
    except Exception as e:
        print(f"Association rules error: {str(e)}")
    
    # Fallback: show related products from same category if no AI recommendations
    if not frequently_bought_together:
        related_products = Product.objects.filter(
            product_category=product.product_category
        ).exclude(id=product.id)[:4]
        frequently_bought_together = [{'product': p, 'confidence': None, 'lift': None} for p in related_products]
    
    # Get all categories for navbar dropdown
    all_categories = Product.objects.values_list('product_category', flat=True).distinct().order_by('product_category')
    
    context = {
        'product': product,
        'frequently_bought_together': frequently_bought_together,
        'all_categories': all_categories,
    }
    return render(request, 'ecommerce/product.html', context)

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # Use AI to predict preferred category based on demographic data
                try:
                    customer = user.customer
                    predictor = get_category_predictor()
                    
                    # Prepare data for prediction
                    customer_data = {
                        'age': customer.age,
                        'household_size': customer.household_size,
                        'has_children': 1 if customer.has_children else 0,
                        'monthly_income_sgd': float(customer.monthly_income_sgd),
                        'gender': customer.gender,
                        'employment_status': customer.employment_status,
                        'occupation': customer.occupation,
                        'education': customer.education
                    }
                    
                    # Predict and update customer's preferred category
                    predicted_category = predictor.predict_category(customer_data)
                    customer.preferred_category = predicted_category
                    customer.save()
                    
                    print(f"✅ AI Prediction for {user.email}: {predicted_category}")
                    
                    messages.success(
                        request, 
                        f'Account created successfully! We\'ve personalized your experience with {predicted_category} recommendations. Please login with your new credentials.'
                    )
                except Exception as e:
                    # If AI prediction fails, still allow signup but log the error
                    messages.success(request, f'Account created successfully! Please login with your new credentials.')
                    import traceback
                    print(f"❌ AI prediction error: {str(e)}")
                    print(traceback.format_exc())
                
                # Redirect to login page instead of auto-login
                return redirect('login')
            except Exception as e:
                messages.error(request, f'An error occurred while creating your account. Please try again.')
                print(f"❌ Signup error: {str(e)}")
                import traceback
                print(traceback.format_exc())
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f"{field_label}: {error}")
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


def search_products(request):
    """Search products by name or SKU with keyword highlighting"""
    query = request.GET.get('search', '').strip()
    
    if not query:
        return redirect('home')
    
    # Search in product name, SKU, and description
    products = Product.objects.filter(
        Q(product_name__icontains=query) |
        Q(sku_code__icontains=query) |
        Q(product_description__icontains=query)
    )
    
    # Get filter parameters
    sort_by = request.GET.get('sort', 'relevance')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    min_rating = request.GET.get('min_rating', '')
    category_filter = request.GET.get('category', '')
    
    # Apply category filter
    if category_filter:
        products = products.filter(product_category=category_filter)
    
    # Apply price filters
    if min_price:
        try:
            products = products.filter(unit_price__gte=Decimal(min_price))
        except:
            pass
    
    if max_price:
        try:
            products = products.filter(unit_price__lte=Decimal(max_price))
        except:
            pass
    
    # Apply rating filter
    if min_rating:
        try:
            products = products.filter(product_rating__gte=Decimal(min_rating))
        except:
            pass
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('unit_price')
    elif sort_by == 'price_high':
        products = products.order_by('-unit_price')
    elif sort_by == 'rating':
        products = products.order_by('-product_rating')
    elif sort_by == 'name':
        products = products.order_by('product_name')
    else:  # relevance - prioritize name matches over description
        products = products.order_by('-product_rating')
    
    # Pagination - 12 products per page
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all unique categories for filtering
    all_categories = Product.objects.values_list('product_category', flat=True).distinct().order_by('product_category')
    
    # Get categories from search results
    result_categories = products.values_list('product_category', flat=True).distinct().order_by('product_category')
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'all_categories': all_categories,
        'result_categories': result_categories,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
        'min_rating': min_rating,
        'category_filter': category_filter,
        'total_results': paginator.count,
    }
    
    return render(request, 'ecommerce/search.html', context)


def category_view(request, category_name):
    """Display products in a category with filters and pagination"""
    # Get all products in this category
    products = Product.objects.filter(product_category=category_name)
    
    # Get filter parameters
    sort_by = request.GET.get('sort', 'name')  # default: name
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    min_rating = request.GET.get('min_rating', '')
    
    # Apply price filters
    if min_price:
        try:
            products = products.filter(unit_price__gte=Decimal(min_price))
        except:
            pass
    
    if max_price:
        try:
            products = products.filter(unit_price__lte=Decimal(max_price))
        except:
            pass
    
    # Apply rating filter
    if min_rating:
        try:
            products = products.filter(product_rating__gte=Decimal(min_rating))
        except:
            pass
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('unit_price')
    elif sort_by == 'price_high':
        products = products.order_by('-unit_price')
    elif sort_by == 'rating':
        products = products.order_by('-product_rating')
    else:  # default to name
        products = products.order_by('product_name')
    
    # Pagination - 12 products per page
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all unique categories for the sidebar
    all_categories = Product.objects.values_list('product_category', flat=True).distinct().order_by('product_category')
    
    context = {
        'category_name': category_name,
        'page_obj': page_obj,
        'all_categories': all_categories,
        'sort_by': sort_by,
        'min_price': min_price,
        'max_price': max_price,
        'min_rating': min_rating,
        'total_products': paginator.count,
    }
    
    return render(request, 'ecommerce/category.html', context)


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
    
    # Use AI to get "Complete the Set" recommendations based on cart items
    cart_recommendations = []
    recommendations_type = None  # Track if AI or fallback
    
    if cart.items.exists():
        try:
            recommender = get_product_recommender()
            cart_skus = [item.product.sku_code for item in cart.items.all()]
            recommended_skus = recommender.get_cart_recommendations(cart_skus, top_n=4)
            
            # Fetch product objects for recommendations
            for sku in recommended_skus:
                try:
                    rec_product = Product.objects.get(sku_code=sku)
                    cart_recommendations.append(rec_product)
                except Product.DoesNotExist:
                    continue
            
            if cart_recommendations:
                recommendations_type = 'ai'
                print(f"🤖 AI found {len(cart_recommendations)} cart recommendations")
            
        except Exception as e:
            print(f"Cart recommendations error: {str(e)}")
        
        # Fallback: If no AI recommendations, show related products from cart categories
        if not cart_recommendations:
            print(f"💡 No AI recommendations, using category fallback")
            recommendations_type = 'category'
            
            # Get categories from cart items
            cart_categories = set(item.product.product_category for item in cart.items.all())
            cart_product_ids = [item.product.id for item in cart.items.all()]
            
            # Find related products from same categories, excluding items already in cart
            for category in cart_categories:
                category_products = Product.objects.filter(
                    product_category=category
                ).exclude(
                    id__in=cart_product_ids
                ).order_by('-product_rating')[:2]  # 2 per category
                
                cart_recommendations.extend(list(category_products))
            
            # Limit to 4 total recommendations
            cart_recommendations = cart_recommendations[:4]
            print(f"   Found {len(cart_recommendations)} category-based recommendations")
    
    context = {
        'cart': cart,
        'cart_recommendations': cart_recommendations,
        'recommendations_type': recommendations_type,
    }
    return render(request, 'ecommerce/cart.html', context)


@login_required
def add_to_cart(request, sku):
    """Add a product to the cart"""
    if request.method == 'POST':
        product = get_object_or_404(Product, sku_code=sku)
        cart = get_or_create_cart(request.user)
        
        try:
            quantity = int(request.POST.get('quantity', 1))
            
            # Validate quantity
            if quantity < 1:
                messages.error(request, 'Quantity must be at least 1.')
                return redirect('product_detail', sku=sku)
            
            if quantity > 100:
                messages.error(request, 'Maximum quantity per order is 100.')
                return redirect('product_detail', sku=sku)
            
            # Check stock availability
            if quantity > product.quantity_on_hand:
                messages.error(request, f'Sorry, only {product.quantity_on_hand} items available in stock.')
                return redirect('product_detail', sku=sku)
            
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity specified.')
            return redirect('product_detail', sku=sku)
        
        # Check if product already in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            
            # Check if new quantity exceeds stock
            if new_quantity > product.quantity_on_hand:
                messages.error(request, f'Cannot add more items. Only {product.quantity_on_hand} available (you have {cart_item.quantity} in cart).')
                return redirect('product_detail', sku=sku)
            
            cart_item.quantity = new_quantity
            cart_item.save()
        
        messages.success(request, f'{product.product_name} added to cart!')
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{product.product_name} added to cart!',
                'cart_total': cart.total_items
            })
        
        # Check if request came from cart page (recommendations)
        from_cart = request.POST.get('from_cart', False)
        if from_cart:
            return redirect('cart_view')
        
        return redirect('product_detail', sku=sku)
    
    return redirect('home')


@login_required
def update_cart_item(request, item_id):
    """Update quantity of a cart item"""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        try:
            quantity = int(request.POST.get('quantity', 1))
            
            # Validate quantity
            if quantity < 0:
                messages.error(request, 'Invalid quantity.')
                return redirect('cart_view')
            
            if quantity == 0:
                cart_item.delete()
                messages.success(request, 'Item removed from cart!')
            else:
                # Check stock availability
                if quantity > cart_item.product.quantity_on_hand:
                    messages.error(request, f'Sorry, only {cart_item.product.quantity_on_hand} items available in stock.')
                    return redirect('cart_view')
                
                if quantity > 100:
                    messages.error(request, 'Maximum quantity per item is 100.')
                    return redirect('cart_view')
                
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, 'Cart updated successfully!')
                
        except (ValueError, TypeError):
            messages.error(request, 'Invalid quantity specified.')
            return redirect('cart_view')
        
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


@login_required
def profile(request):
    """User profile page with update and delete functionality"""
    customer = request.user.customer
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update':
            # Update profile information
            try:
                user = request.user
                user.first_name = request.POST.get('first_name')
                user.last_name = request.POST.get('last_name')
                user.email = request.POST.get('email')
                user.username = request.POST.get('email')  # Username is email
                user.save()
                
                # Update customer information
                customer.age = int(request.POST.get('age'))
                customer.gender = request.POST.get('gender')
                customer.employment_status = request.POST.get('employment_status')
                customer.occupation = request.POST.get('occupation')
                customer.education = request.POST.get('education')
                customer.household_size = int(request.POST.get('household_size'))
                customer.has_children = request.POST.get('has_children') == '1'
                customer.monthly_income_sgd = Decimal(request.POST.get('monthly_income_sgd'))
                customer.save()
                
                # Re-predict preferred category with updated info
                try:
                    predictor = get_category_predictor()
                    customer_data = {
                        'age': customer.age,
                        'household_size': customer.household_size,
                        'has_children': 1 if customer.has_children else 0,
                        'monthly_income_sgd': float(customer.monthly_income_sgd),
                        'gender': customer.gender,
                        'employment_status': customer.employment_status,
                        'occupation': customer.occupation,
                        'education': customer.education
                    }
                    predicted_category = predictor.predict_category(customer_data)
                    customer.preferred_category = predicted_category
                    customer.save()
                    
                    messages.success(
                        request, 
                        f'Profile updated successfully! Your AI preference has been updated to {predicted_category}.'
                    )
                    print(f"✅ Profile updated for {user.email}: New category = {predicted_category}")
                except Exception as e:
                    messages.success(request, 'Profile updated successfully!')
                    print(f"⚠️ AI prediction failed during profile update: {str(e)}")
                
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
                print(f"❌ Profile update error: {str(e)}")
        
        elif action == 'change_password':
            # Change password
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not all([current_password, new_password, confirm_password]):
                messages.error(request, 'All password fields are required.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            elif not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                # Re-login user after password change
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')
                print(f"✅ Password changed for {request.user.email}")
        
        elif action == 'delete_account':
            # Delete account
            delete_password = request.POST.get('delete_password')
            
            if not request.user.check_password(delete_password):
                messages.error(request, 'Incorrect password. Account not deleted.')
            else:
                # Delete user (will cascade delete customer and cart)
                username = request.user.email
                request.user.delete()
                messages.success(request, 'Your account has been permanently deleted. We\'re sorry to see you go.')
                print(f"🗑️ Account deleted: {username}")
                return redirect('home')
        
        return redirect('profile')
    
    context = {
        'customer': customer,
    }
    return render(request, 'ecommerce/profile.html', context)