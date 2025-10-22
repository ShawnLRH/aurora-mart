from django.shortcuts import render
from .models import Product

def home(request):
    products = Product.objects.all()
    featured_products = products[:4]
    popular_products = products[4:8]
    context = {
        'featured_products': featured_products,
        'popular_products': popular_products,
    }
    return render(request, 'ecommerce/home.html', context)