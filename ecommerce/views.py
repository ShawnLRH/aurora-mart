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
    from django.core.paginator import Paginator
    from .models import Review
    
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
    
    # Get reviews for this product
    reviews = Review.objects.filter(product=product).select_related('user')
    
    # Calculate rating statistics
    from django.db.models import Count
    rating_stats = reviews.values('rating').annotate(count=Count('rating')).order_by('-rating')
    total_reviews = reviews.count()
    
    # Calculate percentages for rating stats
    rating_stats_with_percent = []
    for stat in rating_stats:
        percentage = (stat['count'] * 100 / total_reviews) if total_reviews > 0 else 0
        rating_stats_with_percent.append({
            'rating': stat['rating'],
            'count': stat['count'],
            'percentage': round(percentage, 1)
        })
    
    # Pagination for reviews
    paginator = Paginator(reviews, 5)
    page_number = request.GET.get('page', 1)
    reviews_page = paginator.get_page(page_number)
    
    # Get all categories for navbar dropdown
    all_categories = Product.objects.values_list('product_category', flat=True).distinct().order_by('product_category')
    
    context = {
        'product': product,
        'frequently_bought_together': frequently_bought_together,
        'all_categories': all_categories,
        'reviews': reviews_page,
        'total_reviews': total_reviews,
        'rating_stats': rating_stats_with_percent,
    }
    return render(request, 'ecommerce/product.html', context)

def signup(request):
    """Step 1: Collect user data and send verification email"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                # Store form data temporarily
                from .models import EmailVerification
                from django.core.mail import send_mail
                from django.conf import settings
                import json
                
                email = form.cleaned_data['email']
                
                # Check if there's a recent verification pending for this email
                existing_verification = EmailVerification.objects.filter(
                    email=email,
                    is_verified=False
                ).order_by('-created_at').first()
                
                # If exists and not expired, resend the same code
                if existing_verification and not existing_verification.is_expired():
                    verification = existing_verification
                    messages.info(request, 'A verification code has already been sent to your email. Please check your inbox.')
                else:
                    # Create new verification record
                    user_data = {
                        'full_name': form.cleaned_data['full_name'],
                        'email': form.cleaned_data['email'],
                        'password': form.cleaned_data['password1'],
                        'age': form.cleaned_data['age'],
                        'gender': form.cleaned_data['gender'],
                        'employment_status': form.cleaned_data['employment_status'],
                        'occupation': form.cleaned_data['occupation'],
                        'education': form.cleaned_data['education'],
                        'household_size': form.cleaned_data['household_size'],
                        'has_children': form.cleaned_data['has_children'],
                        'monthly_income_sgd': str(form.cleaned_data['monthly_income_sgd']),
                    }
                    
                    verification = EmailVerification.objects.create(
                        email=email,
                        user_data=user_data
                    )
                    
                    # Send verification email
                    try:
                        subject = 'Aurora-Mart Email Verification Code'
                        message = f'''
Hello {user_data['full_name']},

Welcome to Aurora-Mart! 

Your verification code is: {verification.verification_code}

This code will expire in 15 minutes.

If you didn't request this, please ignore this email.

Best regards,
Aurora-Mart Team
'''
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [email],
                            fail_silently=False,
                        )
                        
                        print(f"📧 Verification email sent to {email}")
                        print(f"🔑 Verification code: {verification.verification_code}")
                        
                    except Exception as e:
                        print(f"❌ Email sending failed: {str(e)}")
                        # For development, still proceed
                        pass
                    
                    messages.success(
                        request,
                        f'A 6-digit verification code has been sent to {email}. Please check your inbox and enter the code to complete signup.'
                    )
                
                # Redirect to verification page
                return redirect('verify_email', verification_id=verification.id)
                
            except Exception as e:
                messages.error(request, f'An error occurred while processing your signup. Please try again.')
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


def verify_email(request, verification_id):
    """Step 2: Verify email with 6-digit code"""
    from .models import EmailVerification
    from django.utils import timezone
    
    try:
        verification = EmailVerification.objects.get(id=verification_id)
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('signup')
    
    # Check if already verified
    if verification.is_verified:
        messages.info(request, 'This email has already been verified. Please login.')
        return redirect('login')
    
    if request.method == 'POST':
        entered_code = request.POST.get('verification_code', '').strip()
        
        # Check max attempts
        if verification.attempts >= 5:
            messages.error(request, 'Too many failed attempts. Please sign up again.')
            verification.delete()
            return redirect('signup')
        
        verification.attempts += 1
        verification.save()
        
        if entered_code == verification.verification_code:
            # Code is correct - create the user account
            try:
                from django.contrib.auth.models import User
                from .models import Customer
                import json
                
                user_data = verification.user_data
                
                # Create user
                full_name_parts = user_data['full_name'].split()
                first_name = full_name_parts[0]
                last_name = ' '.join(full_name_parts[1:]) if len(full_name_parts) > 1 else ''
                
                user = User.objects.create_user(
                    username=user_data['email'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create customer profile
                customer = Customer.objects.create(
                    user=user,
                    age=user_data['age'],
                    gender=user_data['gender'],
                    employment_status=user_data['employment_status'],
                    occupation=user_data['occupation'],
                    education=user_data['education'],
                    household_size=user_data['household_size'],
                    has_children=user_data['has_children'],
                    monthly_income_sgd=user_data['monthly_income_sgd'],
                    preferred_category=''
                )
                
                # Use AI to predict preferred category
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
                    
                    print(f"✅ AI Prediction for {user.email}: {predicted_category}")
                    
                    messages.success(
                        request,
                        f'Account created successfully! We\'ve personalized your experience with {predicted_category} recommendations. Please login with your new credentials.'
                    )
                except Exception as e:
                    messages.success(request, 'Account created successfully! Please login with your new credentials.')
                    print(f"❌ AI prediction error: {str(e)}")
                
                # Mark verification as complete
                verification.is_verified = True
                verification.save()
                
                # Redirect to login
                return redirect('login')
                
            except Exception as e:
                messages.error(request, f'An error occurred while creating your account. Please try again.')
                print(f"❌ Account creation error: {str(e)}")
                import traceback
                print(traceback.format_exc())
        else:
            remaining_attempts = 5 - verification.attempts
            if remaining_attempts > 0:
                messages.error(request, f'Invalid verification code. You have {remaining_attempts} attempt(s) remaining.')
            else:
                messages.error(request, 'Too many failed attempts. Please sign up again.')
                verification.delete()
                return redirect('signup')
    
    # Calculate time remaining
    now = timezone.now()
    time_remaining = (verification.expires_at - now).total_seconds()
    is_expired = time_remaining <= 0
    
    context = {
        'verification': verification,
        'email': verification.email,
        'expires_at': verification.expires_at.isoformat(),  # ISO format for JavaScript
        'is_expired': is_expired,
        'time_remaining_seconds': max(0, int(time_remaining)),
    }
    return render(request, 'ecommerce/verify_email.html', context)


def resend_verification_code(request, verification_id):
    """Resend verification code with new 6-digit code"""
    from .models import EmailVerification
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils import timezone
    from datetime import timedelta
    import random
    
    try:
        verification = EmailVerification.objects.get(id=verification_id)
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('signup')
    
    # Check if already verified
    if verification.is_verified:
        messages.info(request, 'This email has already been verified. Please login.')
        return redirect('login')
    
    # Generate new code and reset expiration
    verification.verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    verification.expires_at = timezone.now() + timedelta(minutes=15)
    verification.attempts = 0  # Reset attempts
    verification.save()
    
    # Send new verification email
    try:
        user_data = verification.user_data
        subject = 'Aurora-Mart Email Verification Code (Resent)'
        message = f'''
Hello {user_data['full_name']},

Here is your NEW verification code: {verification.verification_code}

This code will expire in 15 minutes.

If you didn't request this, please ignore this email.

Best regards,
Aurora-Mart Team
'''
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [verification.email],
            fail_silently=False,
        )
        
        print(f"📧 NEW verification email sent to {verification.email}")
        print(f"🔑 NEW verification code: {verification.verification_code}")
        
        messages.success(request, 'A new verification code has been sent to your email!')
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        messages.warning(request, 'New code generated but email sending failed. Check console for the code.')
    
    return redirect('verify_email', verification_id=verification_id)


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


def contact_support(request):
    from .forms import SupportTicketForm
    from .models import SupportTicket
    
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = SupportTicket.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
                status='OPEN'
            )
            messages.success(request, f'Your support ticket #{ticket.id} has been submitted successfully! We will respond to your email shortly.')
            return redirect('contact_support')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['name'] = request.user.get_full_name() or request.user.username
            initial_data['email'] = request.user.email
        form = SupportTicketForm(initial=initial_data)
    
    context = {
        'form': form,
    }
    return render(request, 'ecommerce/contact_support.html', context)


@login_required
def checkout(request):
    from .models import Cart, Address
    
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart_view')
    
    if cart.total_items == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart_view')
    
    # Get user's saved addresses
    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()
    
    # Calculate order totals
    from decimal import Decimal
    subtotal = cart.subtotal
    shipping_fee = Decimal('5.00') if subtotal < 50 else Decimal('0.00')  # Free shipping over $50
    tax = (subtotal * Decimal('0.09')).quantize(Decimal('0.01'))  # 9% tax
    total = subtotal + shipping_fee + tax
    
    context = {
        'cart': cart,
        'addresses': addresses,
        'default_address': default_address,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'tax': tax,
        'total': total,
    }
    return render(request, 'ecommerce/checkout.html', context)


@login_required
def process_checkout(request):
    from .models import Cart, Order, OrderItem, Product, Customer, Address
    from django.utils import timezone
    from decimal import Decimal
    
    if request.method != 'POST':
        return redirect('checkout')
    
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart_view')
    
    if cart.total_items == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart_view')
    
    # Get form data
    use_saved_address = request.POST.get('use_saved_address')
    save_address = request.POST.get('save_address') == 'on'
    payment_method = request.POST.get('payment_method')
    
    # Validate payment method
    valid_methods = ['CREDIT_CARD', 'PAYPAL', 'BANK_TRANSFER', 'CASH_ON_DELIVERY']
    if payment_method not in valid_methods:
        messages.error(request, 'Please select a valid payment method.')
        return redirect('checkout')
    
    # Get address data
    if use_saved_address:
        try:
            address = Address.objects.get(id=use_saved_address, user=request.user)
            full_name = address.full_name
            phone = address.phone
            address_line1 = address.address_line1
            address_line2 = address.address_line2
            city = address.city
            state = address.state
            postal_code = address.postal_code
            country = address.country
        except Address.DoesNotExist:
            messages.error(request, 'Selected address not found.')
            return redirect('checkout')
    else:
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address_line1 = request.POST.get('address_line1', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', 'Singapore').strip()
        
        # Validate address fields
        if not all([full_name, phone, address_line1, city, state, postal_code, country]):
            messages.error(request, 'Please fill in all required address fields.')
            return redirect('checkout')
        
        # Save new address if requested
        if save_address:
            Address.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                is_default=not Address.objects.filter(user=request.user).exists()
            )
    
    # Calculate totals
    subtotal = cart.subtotal
    shipping_fee = Decimal('5.00') if subtotal < 50 else Decimal('0.00')
    tax = (subtotal * Decimal('0.09')).quantize(Decimal('0.01'))
    total = subtotal + shipping_fee + tax
    
    # Check stock availability
    for item in cart.items.all():
        if item.product.quantity_on_hand < item.quantity:
            messages.error(request, f'Insufficient stock for {item.product.product_name}. Only {item.product.quantity_on_hand} available.')
            return redirect('cart_view')
    
    # Get or create customer profile
    try:
        customer = Customer.objects.get(user=request.user)
    except Customer.DoesNotExist:
        customer = None
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        customer=customer,
        shipping_full_name=full_name,
        shipping_phone=phone,
        shipping_address_line1=address_line1,
        shipping_address_line2=address_line2,
        shipping_city=city,
        shipping_state=state,
        shipping_postal_code=postal_code,
        shipping_country=country,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        tax=tax,
        total_amount=total,
        payment_method=payment_method,
        status='ORDER_RECEIVED'
    )
    
    # Create order items and reduce stock
    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_sku=item.product.sku_code,
            product_name=item.product.product_name,
            quantity=item.quantity,
            unit_price=item.product.unit_price
        )
        
        # Reduce stock
        item.product.quantity_on_hand -= item.quantity
        item.product.save()
        print(f"📦 Stock reduced: {item.product.product_name} - New quantity: {item.product.quantity_on_hand}")
    
    # Clear cart
    cart.items.all().delete()
    
    messages.success(request, f'Order {order.order_id} placed successfully!')
    print(f"✅ Order created: {order.order_id} - Total: ${order.total_amount}")
    
    return redirect('order_confirmation', order_id=order.order_id)


@login_required
def order_confirmation(request, order_id):
    from .models import Order, Product
    from django.db.models import Q
    import random
    
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('order_history')
    
    # Get AI recommendations for "next purchase"
    purchased_skus = [item.product_sku for item in order.items.all()]
    purchased_categories = [item.product.product_category for item in order.items.all() if item.product]
    
    # Get products from same categories
    recommendations = []
    if purchased_categories:
        recommendations = list(Product.objects.filter(
            product_category__in=purchased_categories,
            quantity_on_hand__gt=0
        ).exclude(
            sku_code__in=purchased_skus
        ).order_by('-product_rating', '-quantity_on_hand')[:6])
    
    # If not enough recommendations, add random popular products
    if len(recommendations) < 6:
        additional = list(Product.objects.filter(
            quantity_on_hand__gt=0
        ).exclude(
            sku_code__in=purchased_skus
        ).exclude(
            sku_code__in=[p.sku_code for p in recommendations]
        ).order_by('-product_rating')[:6 - len(recommendations)])
        recommendations.extend(additional)
    
    # Shuffle for variety
    random.shuffle(recommendations)
    
    context = {
        'order': order,
        'recommendations': recommendations[:6],
    }
    return render(request, 'ecommerce/order_confirmation.html', context)


@login_required
def order_history(request):
    from .models import Order
    from django.core.paginator import Paginator
    
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)  # 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'ecommerce/order_history.html', context)


@login_required
def order_detail(request, order_id):
    from .models import Order, Review
    
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('order_history')
    
    # Calculate progress percentage
    progress_map = {
        'ORDER_RECEIVED': 33,
        'ORDER_SENT': 66,
        'DELIVERED': 100,
        'CANCELLED': 0,
    }
    progress = progress_map.get(order.status, 0)
    
    # Get list of products already reviewed from this order
    reviewed_products = Review.objects.filter(
        user=request.user,
        order=order
    ).values_list('product__sku_code', flat=True)
    
    context = {
        'order': order,
        'progress': progress,
        'reviewed_products': list(reviewed_products),
    }
    return render(request, 'ecommerce/order_detail.html', context)


@login_required
def reorder(request, order_id):
    from .models import Order, Cart, CartItem
    
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('order_history')
    
    # Get or create cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Add order items to cart
    added_count = 0
    for item in order.items.all():
        if item.product and item.product.quantity_on_hand > 0:
            # Check if item already in cart
            cart_item = cart.items.filter(product=item.product).first()
            if cart_item:
                # Update quantity
                new_quantity = min(cart_item.quantity + item.quantity, item.product.quantity_on_hand)
                cart_item.quantity = new_quantity
                cart_item.save()
            else:
                # Add new item
                CartItem.objects.create(
                    cart=cart,
                    product=item.product,
                    quantity=min(item.quantity, item.product.quantity_on_hand)
                )
            added_count += 1
        else:
            messages.warning(request, f'{item.product_name} is currently out of stock.')
    
    if added_count > 0:
        messages.success(request, f'{added_count} item(s) added to your cart from order {order.order_id}.')
    else:
        messages.error(request, 'No items could be added to cart (all out of stock).')
    
    return redirect('cart_view')


@login_required
def complete_order(request, order_id):
    from .models import Order
    from django.utils import timezone
    
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('order_history')
    
    # Only allow completion if order is delivered
    if order.status != 'DELIVERED':
        messages.error(request, 'Order cannot be marked as received yet.')
        return redirect('order_detail', order_id=order.order_id)
    
    # Mark order as completed
    order.status = 'COMPLETED'
    order.completed_at = timezone.now()
    order.save()
    
    messages.success(request, 'Thank you for confirming receipt! Your order is now completed.')
    print(f"✅ Order {order.order_id} marked as completed by customer")
    
    return redirect('order_detail', order_id=order.order_id)


@login_required
def refund_order(request, order_id):
    from .models import Order
    from django.utils import timezone
    
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('order_history')
    
    # Only allow refund if order is delivered
    if order.status != 'DELIVERED':
        messages.error(request, 'Order cannot be refunded at this stage.')
        return redirect('order_detail', order_id=order.order_id)
    
    if request.method == 'POST':
        refund_reason = request.POST.get('refund_reason', '').strip()
        
        if not refund_reason:
            messages.error(request, 'Please provide a reason for the refund.')
            return redirect('refund_order', order_id=order.order_id)
        
        # Process refund: restore stock for all items
        for item in order.items.all():
            if item.product:
                item.product.quantity_on_hand += item.quantity
                item.product.save()
                print(f"📦 Stock restored: {item.product.product_name} +{item.quantity} = {item.product.quantity_on_hand}")
        
        # Update order status
        order.status = 'REFUNDED'
        order.refunded_at = timezone.now()
        order.refund_reason = refund_reason
        order.save()
        
        messages.success(request, f'Your refund request for order {order.order_id} has been processed. Stock has been restored.')
        print(f"💰 Order {order.order_id} refunded - Reason: {refund_reason[:50]}...")
        
        return redirect('order_detail', order_id=order.order_id)
    
    # GET request - show refund form
    context = {
        'order': order,
    }
    return render(request, 'ecommerce/refund_order.html', context)


@login_required
def create_review(request, order_id, product_sku):
    from .models import Order, Product, Review
    
    try:
        order = Order.objects.get(order_id=order_id, user=request.user)
        product = Product.objects.get(sku_code=product_sku)
    except (Order.DoesNotExist, Product.DoesNotExist):
        messages.error(request, 'Order or product not found.')
        return redirect('order_history')
    
    # Only allow reviews for delivered or completed orders
    if order.status not in ['DELIVERED', 'COMPLETED']:
        messages.error(request, 'You can only review products from delivered orders.')
        return redirect('order_detail', order_id=order.order_id)
    
    # Check if product was in this order
    order_item = order.items.filter(product=product).first()
    if not order_item:
        messages.error(request, 'This product was not in your order.')
        return redirect('order_detail', order_id=order.order_id)
    
    # Check if review already exists
    existing_review = Review.objects.filter(product=product, user=request.user, order=order).first()
    if existing_review:
        messages.warning(request, 'You have already reviewed this product from this order.')
        return redirect('order_detail', order_id=order.order_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title', '').strip()
        comment = request.POST.get('comment', '').strip()
        
        # Validation
        if not rating or not title or not comment:
            messages.error(request, 'Please fill in all fields.')
            return redirect('create_review', order_id=order_id, product_sku=product_sku)
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            messages.error(request, 'Invalid rating value.')
            return redirect('create_review', order_id=order_id, product_sku=product_sku)
        
        # Create review
        Review.objects.create(
            product=product,
            user=request.user,
            order=order,
            rating=rating,
            title=title,
            comment=comment
        )
        
        # Update product rating (calculate average)
        from django.db.models import Avg
        avg_rating = Review.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg']
        if avg_rating:
            product.product_rating = round(avg_rating, 1)
            product.save()
        
        messages.success(request, 'Thank you for your review!')
        return redirect('order_detail', order_id=order.order_id)
    
    # GET request - show review form
    context = {
        'order': order,
        'product': product,
        'order_item': order_item,
    }
    return render(request, 'ecommerce/create_review.html', context)


@login_required
def my_reviews(request):
    from .models import Review
    from django.core.paginator import Paginator
    
    reviews = Review.objects.filter(user=request.user)
    
    # Pagination
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reviews': page_obj,
    }
    return render(request, 'ecommerce/my_reviews.html', context)