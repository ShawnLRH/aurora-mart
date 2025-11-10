import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aurora.settings')
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@auroramart.com', 'admin123')
    print('✅ Superuser created successfully!')
    print('Username: admin')
    print('Email: admin@auroramart.com')
    print('Password: admin123')
else:
    print('⚠️  Admin user already exists')
