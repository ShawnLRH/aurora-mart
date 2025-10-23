from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from django.contrib.auth import login
from .forms import SignUpForm

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