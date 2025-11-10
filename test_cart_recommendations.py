#!/usr/bin/env python3
"""
Test script to verify "Complete the Set" cart recommendations
"""
import os
import sys
sys.path.insert(0, '/Users/shawnlee/IdeaProjects/aurora-mart')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aurora.settings')
import django
django.setup()

from django.contrib.auth.models import User
from ecommerce.models import Product, Cart, CartItem
from ecommerce.ai_utils import get_product_recommender

print("=" * 60)
print("COMPLETE THE SET - CART RECOMMENDATIONS TEST")
print("=" * 60)

# Get test user
user = User.objects.filter(email='happyshawnlee@gmail.com').first()
if not user:
    print("❌ Test user not found. Please create an account first.")
    sys.exit(1)

print(f"\n✅ Testing with user: {user.email}")

# Clear existing cart
cart, _ = Cart.objects.get_or_create(user=user)
cart.items.all().delete()
print(f"✅ Cleared existing cart")

# Add products that we know have association rules
test_skus = ['AIA-JM4T8BP6', 'ACC-N6Q7NC85']
print(f"\n📦 Adding products to cart:")

for sku in test_skus:
    product = Product.objects.filter(sku_code=sku).first()
    if product:
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        print(f"  ✅ Added: {product.product_name} ({sku})")
    else:
        print(f"  ❌ Product not found: {sku}")

# Test recommendations
print(f"\n🤖 Testing AI Recommendations:")
recommender = get_product_recommender()
cart_items = cart.items.all()
cart_skus = [item.product.sku_code for item in cart_items]

print(f"  Cart contains: {cart_skus}")

recommendations = recommender.get_cart_recommendations(cart_skus, top_n=4)
print(f"  AI returned {len(recommendations)} recommendations")

if recommendations:
    print(f"\n  ⭐ Recommended products:")
    for sku in recommendations:
        product = Product.objects.filter(sku_code=sku).first()
        if product:
            print(f"    - {product.product_name} ({sku})")
            print(f"      Category: {product.product_category}")
            print(f"      Price: ${product.unit_price}")
        else:
            print(f"    - {sku} (not in database)")
else:
    print(f"  ⚠️  No recommendations found")

print("\n" + "=" * 60)
print("TEST VERIFICATION")
print("=" * 60)
print(f"✅ Cart has {cart.items.count()} items")
print(f"✅ AI returned {len(recommendations)} recommendations")
print(f"\nTo see in browser:")
print(f"1. Visit: http://127.0.0.1:8000/cart/")
print(f"2. Look for 'Complete the Set' section")
print(f"3. Should show {len(recommendations)} recommended products")
print("=" * 60)
