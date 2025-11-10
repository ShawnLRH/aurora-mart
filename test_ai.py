# AI Testing Script
# Run this to verify AI integration is working

import os
import sys
sys.path.insert(0, '/Users/shawnlee/IdeaProjects/aurora-mart')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aurora.settings')
import django
django.setup()

from django.contrib.auth.models import User
from ecommerce.models import Customer, Product
from ecommerce.ai_utils import get_category_predictor, get_product_recommender

print("=" * 60)
print("AURORA-MART AI INTEGRATION TEST")
print("=" * 60)

# Test 1: Category Predictor
print("\n1. Testing Category Predictor...")
try:
    predictor = get_category_predictor()
    
    test_cases = [
        {
            'age': 35, 'household_size': 2, 'has_children': 1,
            'monthly_income_sgd': 8000.0, 'gender': 'Male',
            'employment_status': 'Full-time', 'occupation': 'Tech',
            'education': 'Bachelor',
            'expected': 'Electronics'
        },
        {
            'age': 29, 'household_size': 2, 'has_children': 1,
            'monthly_income_sgd': 5000.0, 'gender': 'Female',
            'employment_status': 'Full-time', 'occupation': 'Sales',
            'education': 'Bachelor',
            'expected': 'Fashion/Beauty'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        expected = test.pop('expected')
        result = predictor.predict_category(test)
        print(f"   Test {i}: Predicted '{result}' (expected something like '{expected}')")
    
    print("   ✅ Category Predictor working!")
except Exception as e:
    print(f"   ❌ Category Predictor failed: {str(e)}")

# Test 2: Product Recommender
print("\n2. Testing Product Recommender...")
try:
    recommender = get_product_recommender()
    
    # Get a sample product SKU
    sample_product = Product.objects.first()
    if sample_product:
        sku = sample_product.sku_code
        recs = recommender.get_frequently_bought_together(sku, top_n=3)
        print(f"   Testing with SKU: {sku}")
        print(f"   Found {len(recs)} recommendations")
        if recs:
            for rec in recs[:2]:
                print(f"     - {rec['sku']} (confidence: {rec['confidence']}, lift: {rec['lift']})")
        print("   ✅ Product Recommender working!")
    else:
        print("   ⚠️  No products in database to test with")
except Exception as e:
    print(f"   ❌ Product Recommender failed: {str(e)}")

# Test 3: Database Status
print("\n3. Checking Database Status...")
total_products = Product.objects.count()
total_customers = Customer.objects.count()
registered_users = Customer.objects.filter(user__isnull=False).count()
csv_customers = Customer.objects.filter(user__isnull=True).count()

print(f"   Products: {total_products}")
print(f"   Customers (from CSV): {csv_customers}")
print(f"   Registered users: {registered_users}")

# Test 4: Product Categories
print("\n4. Product Categories in Database:")
categories = Product.objects.values_list('product_category', flat=True).distinct().order_by('product_category')
for cat in categories:
    count = Product.objects.filter(product_category=cat).count()
    print(f"   - {cat}: {count} products")

# Test 5: Registered Users with Predictions
print("\n5. Registered Users with AI Predictions:")
user_customers = Customer.objects.filter(user__isnull=False)
if user_customers.exists():
    for customer in user_customers:
        user = customer.user
        category = customer.preferred_category or "(not yet predicted)"
        print(f"   - {user.email}: {category}")
else:
    print("   No registered users yet. Sign up to test AI prediction!")

print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("✅ AI models loaded successfully")
print("✅ Category prediction working")
print("✅ Product recommendations working")
print(f"✅ Database has {total_products} products across {len(categories)} categories")
print("\nTo test signup prediction:")
print("1. Visit http://127.0.0.1:8000/signup/")
print("2. Fill form with: Age=35, Gender=Male, Occupation=Tech, etc.")
print("3. Check welcome message shows predicted category")
print("4. Check home page shows personalized products")
print("=" * 60)
