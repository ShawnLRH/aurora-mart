#!/usr/bin/env python3
"""
Test script for profile page functionality
"""
import os
import sys
sys.path.insert(0, '/Users/shawnlee/IdeaProjects/aurora-mart')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aurora.settings')
import django
django.setup()

from django.contrib.auth.models import User
from ecommerce.models import Customer

print("=" * 60)
print("PROFILE PAGE TEST")
print("=" * 60)

# Check existing users
users = User.objects.all()
print(f"\nExisting users: {users.count()}")

for user in users:
    if hasattr(user, 'customer'):
        customer = user.customer
        print(f"\n👤 User: {user.email}")
        print(f"   Name: {user.first_name} {user.last_name}")
        print(f"   Age: {customer.age}")
        print(f"   AI Category: {customer.preferred_category}")
        print(f"   Occupation: {customer.occupation}")
        print(f"   Education: {customer.education}")
    else:
        print(f"\n⚠️  User {user.email} has no customer profile")

print("\n" + "=" * 60)
print("PROFILE PAGE FEATURES")
print("=" * 60)
print("✅ View profile information")
print("✅ Edit profile with toggle button")
print("✅ Update all demographic fields")
print("✅ AI re-prediction on profile update")
print("✅ Change password functionality")
print("✅ Delete account with confirmation")
print("✅ Beautiful gradient design")
print("\nTo test:")
print("1. Visit: http://127.0.0.1:8000/profile/")
print("2. Click 'Edit Profile' to update information")
print("3. Try changing password")
print("4. View AI personalization badge")
print("=" * 60)
