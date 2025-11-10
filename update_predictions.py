#!/usr/bin/env python3
"""
Script to update existing users with AI-predicted preferred categories
"""
import os
import sys
sys.path.insert(0, '/Users/shawnlee/IdeaProjects/aurora-mart')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aurora.settings')
import django
django.setup()

from ecommerce.models import Customer
from ecommerce.ai_utils import get_category_predictor

print("Updating existing users with AI predictions...")
print("=" * 60)

predictor = get_category_predictor()

# Get all customers with users but no predicted category
customers = Customer.objects.filter(user__isnull=False, preferred_category='')

if not customers.exists():
    print("No customers need updates. All have predicted categories!")
else:
    print(f"Found {customers.count()} customers to update\n")
    
    for customer in customers:
        try:
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
            
            # Predict category
            predicted_category = predictor.predict_category(customer_data)
            
            # Update customer
            customer.preferred_category = predicted_category
            customer.save()
            
            print(f"✅ {customer.user.email}: {predicted_category}")
            
        except Exception as e:
            print(f"❌ {customer.user.email}: Error - {str(e)}")

print("\n" + "=" * 60)
print("Update complete!")
print("\nVerify by running:")
print("  python3 manage.py shell -c \"from ecommerce.models import Customer; ")
print("  print([(c.user.email, c.preferred_category) for c in Customer.objects.filter(user__isnull=False)])\"")
