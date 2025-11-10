from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q, F
from ecommerce.models import Product
from .forms import ProductForm, StockAdjustmentForm

@staff_member_required
def admin_dashboard(request):
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(quantity_on_hand__lte=F('reorder_quantity')).count()
    out_of_stock_count = Product.objects.filter(quantity_on_hand=0).count()
    
    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    return render(request, 'adminpanel/dashboard.html', context)

@staff_member_required
def product_list(request):
    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '')
    stock_filter = request.GET.get('stock', '')
    
    products = Product.objects.all()
    
    if search_query:
        products = products.filter(
            Q(sku_code__icontains=search_query) |
            Q(product_name__icontains=search_query) |
            Q(product_category__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(product_category=category_filter)
    
    if stock_filter == 'low':
        products = products.filter(quantity_on_hand__lte=F('reorder_quantity'))
    elif stock_filter == 'out':
        products = products.filter(quantity_on_hand=0)
    
    products = products.order_by('product_name')
    
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    categories = Product.objects.values_list('product_category', flat=True).distinct().order_by('product_category')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'stock_filter': stock_filter,
        'categories': categories,
        'total_products': paginator.count,
    }
    return render(request, 'adminpanel/product_list.html', context)

@staff_member_required
def product_create(request):
    from .models import SystemLog
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                product = form.save()
                
                SystemLog.objects.create(
                    user=request.user,
                    action_type='CREATE',
                    object_type='Product',
                    object_id=product.sku_code,
                    description=f'Created product: {product.product_name} (SKU: {product.sku_code})',
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, f'Product "{product.product_name}" (SKU: {product.sku_code}) created successfully!')
                return redirect('admin_product_list')
            except Exception as e:
                messages.error(request, f'Error creating product: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f"{field_label}: {error}")
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'page_title': 'Create Product',
        'submit_text': 'Create Product',
    }
    return render(request, 'adminpanel/product_form.html', context)

@staff_member_required
def product_edit(request, sku):
    from .models import SystemLog
    
    product = get_object_or_404(Product, sku_code=sku)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            try:
                product = form.save()
                
                SystemLog.objects.create(
                    user=request.user,
                    action_type='UPDATE',
                    object_type='Product',
                    object_id=product.sku_code,
                    description=f'Updated product: {product.product_name} (SKU: {product.sku_code})',
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, f'Product "{product.product_name}" updated successfully!')
                return redirect('admin_product_list')
            except Exception as e:
                messages.error(request, f'Error updating product: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f"{field_label}: {error}")
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'page_title': f'Edit Product - {product.product_name}',
        'submit_text': 'Update Product',
    }
    return render(request, 'adminpanel/product_form.html', context)

@staff_member_required
def product_delete(request, sku):
    from .models import SystemLog
    
    product = get_object_or_404(Product, sku_code=sku)
    
    if request.method == 'POST':
        product_name = product.product_name
        product_sku = product.sku_code
        try:
            product.delete()
            
            SystemLog.objects.create(
                user=request.user,
                action_type='DELETE',
                object_type='Product',
                object_id=product_sku,
                description=f'Deleted product: {product_name} (SKU: {product_sku})',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Product "{product_name}" (SKU: {product_sku}) has been deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting product: {str(e)}')
        return redirect('admin_product_list')
    
    context = {
        'product': product,
    }
    return render(request, 'adminpanel/product_delete.html', context)

@staff_member_required
def stock_adjust(request, sku):
    from .models import SystemLog
    
    product = get_object_or_404(Product, sku_code=sku)
    
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            try:
                old_quantity = product.quantity_on_hand
                new_quantity = form.cleaned_data['quantity_on_hand']
                product.quantity_on_hand = new_quantity
                product.save()
                
                SystemLog.objects.create(
                    user=request.user,
                    action_type='UPDATE',
                    object_type='Product',
                    object_id=str(product.id),
                    description=f'Adjusted stock for "{product.product_name}" from {old_quantity} to {new_quantity}',
                    ip_address=get_client_ip(request)
                )
                
                if new_quantity <= product.reorder_quantity:
                    messages.warning(request, f'Stock for "{product.product_name}" updated to {new_quantity}. Warning: Stock is below reorder threshold ({product.reorder_quantity})!')
                else:
                    messages.success(request, f'Stock for "{product.product_name}" updated from {old_quantity} to {new_quantity}.')
                
                return redirect('admin_product_list')
            except Exception as e:
                messages.error(request, f'Error adjusting stock: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = StockAdjustmentForm(initial={'quantity_on_hand': product.quantity_on_hand})
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'adminpanel/stock_adjust.html', context)

@staff_member_required
def low_stock_alerts(request):
    low_stock_products = Product.objects.filter(
        quantity_on_hand__lte=F('reorder_quantity')
    ).order_by('quantity_on_hand', 'product_name')
    
    paginator = Paginator(low_stock_products, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_alerts': paginator.count,
    }
    return render(request, 'adminpanel/low_stock_alerts.html', context)

@staff_member_required
def product_import_csv(request):
    from .forms import CSVUploadForm
    from .models import SystemLog
    import csv
    import io
    from decimal import Decimal, InvalidOperation
    
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            try:
                decoded_file = csv_file.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                try:
                    csv_file.seek(0)
                    decoded_file = csv_file.read().decode('latin-1')
                except Exception as e:
                    messages.error(request, f'Error reading file: {str(e)}')
                    return redirect('admin_product_import')
            
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            
            imported = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    sku = row.get('sku_code', '').strip()
                    if not sku:
                        errors.append(f"Row {row_num}: Missing SKU code")
                        continue
                    
                    if Product.objects.filter(sku_code=sku).exists():
                        errors.append(f"Row {row_num}: SKU {sku} already exists")
                        continue
                    
                    Product.objects.create(
                        sku_code=sku,
                        product_name=row.get('product_name', '').strip(),
                        product_description=row.get('product_description', '').strip(),
                        product_category=row.get('product_category', '').strip(),
                        product_subcategory=row.get('product_subcategory', '').strip(),
                        quantity_on_hand=int(row.get('quantity_on_hand', 0)),
                        reorder_quantity=int(row.get('reorder_quantity', 0)),
                        unit_price=Decimal(row.get('unit_price', 0)),
                        product_rating=Decimal(row.get('product_rating', 0))
                    )
                    imported += 1
                    
                except (ValueError, InvalidOperation, KeyError) as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    continue
            
            if imported > 0:
                SystemLog.objects.create(
                    user=request.user,
                    action_type='IMPORT',
                    object_type='Product',
                    object_id='',
                    description=f'Imported {imported} products from CSV. {len(errors)} errors encountered.',
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, f'Successfully imported {imported} products!')
            if errors:
                for error in errors[:10]:
                    messages.warning(request, error)
                if len(errors) > 10:
                    messages.warning(request, f'... and {len(errors) - 10} more errors')
            
            return redirect('admin_product_list')
    else:
        form = CSVUploadForm()
    
    context = {
        'form': form,
    }
    return render(request, 'adminpanel/product_import.html', context)

@staff_member_required
def product_export_csv(request):
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="products_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['sku_code', 'product_name', 'product_description', 'product_category', 
                     'product_subcategory', 'quantity_on_hand', 'reorder_quantity', 'unit_price', 'product_rating'])
    
    products = Product.objects.all().order_by('sku_code')
    for product in products:
        writer.writerow([
            product.sku_code,
            product.product_name,
            product.product_description,
            product.product_category,
            product.product_subcategory,
            product.quantity_on_hand,
            product.reorder_quantity,
            product.unit_price,
            product.product_rating
        ])
    
    return response

@staff_member_required
def customer_list(request):
    from ecommerce.models import Customer
    
    search_query = request.GET.get('search', '').strip()
    
    customers = Customer.objects.select_related('user').all()
    
    if search_query:
        customers = customers.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    customers = customers.order_by('-id')
    
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_customers': paginator.count,
    }
    return render(request, 'adminpanel/customer_list.html', context)

@staff_member_required
def customer_edit(request, customer_id):
    from ecommerce.models import Customer
    from .forms import CustomerForm
    from .models import SystemLog
    from ecommerce.ai_utils import get_category_predictor
    
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            try:
                customer = form.save(commit=False)
                
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
                except:
                    pass
                
                customer.save()
                SystemLog.objects.create(
                    user=request.user,
                    action_type='UPDATE',
                    object_type='Customer',
                    object_id=str(customer.id),
                    description=f'Updated customer "{customer.user.email}"',
                    ip_address=get_client_ip(request)
                )
                messages.success(request, f'Customer {customer.user.email} updated successfully!')
                return redirect('admin_customer_list')
            except Exception as e:
                messages.error(request, f'Error updating customer: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f"{field_label}: {error}")
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
    }
    return render(request, 'adminpanel/customer_form.html', context)

@staff_member_required
def customer_delete(request, customer_id):
    from ecommerce.models import Customer
    from .models import SystemLog
    
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        user_email = customer.user.email if customer.user else 'Unknown'
        try:
            if customer.user:
                customer.user.delete()
            else:
                customer.delete()
            
            SystemLog.objects.create(
                user=request.user,
                action_type='DELETE',
                object_type='Customer',
                object_id=str(customer_id),
                description=f'Deleted customer: {user_email}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'Customer {user_email} has been deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting customer: {str(e)}')
        return redirect('admin_customer_list')
    
    context = {
        'customer': customer,
    }
    return render(request, 'adminpanel/customer_delete.html', context)

@staff_member_required
def bulk_price_update(request):
    from .forms import BulkPriceUpdateForm
    from .models import SystemLog
    from decimal import Decimal
    
    if request.method == 'POST':
        form = BulkPriceUpdateForm(request.POST)
        if form.is_valid():
            try:
                category = form.cleaned_data['category']
                percentage = form.cleaned_data['percentage']
                
                products = Product.objects.filter(product_category=category)
                count = products.count()
                
                if count == 0:
                    messages.warning(request, f'No products found in category "{category}".')
                    return redirect('admin_bulk_price_update')
                
                multiplier = Decimal('1') + (percentage / Decimal('100'))
                
                for product in products:
                    old_price = product.unit_price
                    product.unit_price = (old_price * multiplier).quantize(Decimal('0.01'))
                    product.save()
                
                SystemLog.objects.create(
                    user=request.user,
                    action_type='BULK_UPDATE',
                    object_type='Product',
                    object_id=category,
                    description=f'Applied {percentage}% price change to {count} products in category "{category}"',
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, f'Successfully updated prices for {count} products in "{category}" by {percentage}%.')
                return redirect('admin_product_list')
            except Exception as e:
                messages.error(request, f'Error updating prices: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f"{field_label}: {error}")
    else:
        form = BulkPriceUpdateForm()
    
    context = {
        'form': form,
    }
    return render(request, 'adminpanel/bulk_price_update.html', context)

@staff_member_required
def staff_list(request):
    from django.contrib.auth.models import User
    
    staff_users = User.objects.filter(is_staff=True).order_by('-date_joined')
    
    paginator = Paginator(staff_users, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_staff': paginator.count,
    }
    return render(request, 'adminpanel/staff_list.html', context)

@staff_member_required
def staff_create(request):
    from .forms import StaffUserForm
    from django.contrib.auth.models import User
    from .models import SystemLog
    
    if request.method == 'POST':
        form = StaffUserForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    is_staff=True,
                    is_superuser=True
                )
                
                SystemLog.objects.create(
                    user=request.user,
                    action_type='CREATE',
                    object_type='Staff',
                    object_id=str(user.id),
                    description=f'Created staff account: {user.username} ({user.email})',
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, f'Staff account "{user.username}" created successfully!')
                return redirect('admin_staff_list')
            except Exception as e:
                messages.error(request, f'Error creating staff account: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f"{field_label}: {error}")
    else:
        form = StaffUserForm()
    
    context = {
        'form': form,
    }
    return render(request, 'adminpanel/staff_form.html', context)

@staff_member_required
def staff_delete(request, user_id):
    from django.contrib.auth.models import User
    from .models import SystemLog
    
    staff_user = get_object_or_404(User, id=user_id, is_staff=True)
    
    if staff_user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_staff_list')
    
    if request.method == 'POST':
        username = staff_user.username
        try:
            SystemLog.objects.create(
                user=request.user,
                action_type='DELETE',
                object_type='Staff',
                object_id=str(user_id),
                description=f'Deleted staff account: {username}',
                ip_address=get_client_ip(request)
            )
            
            staff_user.delete()
            messages.success(request, f'Staff account "{username}" has been deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting staff account: {str(e)}')
        return redirect('admin_staff_list')
    
    context = {
        'staff_user': staff_user,
    }
    return render(request, 'adminpanel/staff_delete.html', context)

@staff_member_required
def system_logs(request):
    from .models import SystemLog
    
    action_filter = request.GET.get('action', '')
    object_filter = request.GET.get('object', '')
    
    logs = SystemLog.objects.select_related('user').all()
    
    if action_filter:
        logs = logs.filter(action_type=action_filter)
    
    if object_filter:
        logs = logs.filter(object_type__icontains=object_filter)
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    action_choices = SystemLog.ACTION_CHOICES
    
    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'object_filter': object_filter,
        'action_choices': action_choices,
        'total_logs': paginator.count,
    }
    return render(request, 'adminpanel/system_logs.html', context)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@staff_member_required
def support_tickets(request):
    from ecommerce.models import SupportTicket
    
    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('search', '').strip()
    
    tickets = SupportTicket.objects.select_related('user', 'responded_by').all()
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    if search_query:
        tickets = tickets.filter(
            Q(subject__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    tickets = tickets.order_by('-created_at')
    
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_tickets': paginator.count,
    }
    return render(request, 'adminpanel/support_tickets.html', context)


@staff_member_required
def support_ticket_detail(request, ticket_id):
    from ecommerce.models import SupportTicket
    from .models import SystemLog
    from django.utils import timezone
    
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'respond':
            response = request.POST.get('response', '').strip()
            if response:
                ticket.admin_response = response
                ticket.responded_by = request.user
                ticket.responded_at = timezone.now()
                ticket.status = 'RESOLVED'
                ticket.save()
                
                SystemLog.objects.create(
                    user=request.user,
                    action_type='UPDATE',
                    object_type='SupportTicket',
                    object_id=str(ticket.id),
                    description=f'Responded to support ticket #{ticket.id} - {ticket.subject}',
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, 'Email sent!')
            else:
                messages.error(request, 'Response cannot be empty.')
        
        return redirect('admin_support_ticket_detail', ticket_id=ticket.id)
    
    context = {
        'ticket': ticket,
        'status_choices': SupportTicket.STATUS_CHOICES,
    }
    return render(request, 'adminpanel/support_ticket_detail.html', context)
