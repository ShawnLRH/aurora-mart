from django import forms
from ecommerce.models import Product, Customer
from django.core.exceptions import ValidationError
from decimal import Decimal

class ProductForm(forms.ModelForm):
    sku_code = forms.CharField(
        max_length=50,
        required=True,
        label="SKU Code",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter unique SKU code'})
    )
    
    product_name = forms.CharField(
        max_length=200,
        required=True,
        label="Product Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'})
    )
    
    product_description = forms.CharField(
        max_length=1000,
        required=True,
        label="Description",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter product description'})
    )
    
    CATEGORY_CHOICES = [
        ('', 'Select Category'),
        ('Electronics', 'Electronics'),
        ('Fashion - Men', 'Fashion - Men'),
        ('Fashion - Women', 'Fashion - Women'),
        ('Home & Garden', 'Home & Garden'),
        ('Beauty & Personal Care', 'Beauty & Personal Care'),
        ('Sports & Outdoors', 'Sports & Outdoors'),
        ('Toys & Games', 'Toys & Games'),
        ('Books & Media', 'Books & Media'),
        ('Health & Wellness', 'Health & Wellness'),
        ('Automotive', 'Automotive'),
    ]
    product_category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=True,
        label="Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    quantity_on_hand = forms.IntegerField(
        required=True,
        min_value=0,
        label="Stock Quantity",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current stock quantity'})
    )
    
    reorder_quantity = forms.IntegerField(
        required=True,
        min_value=0,
        label="Reorder Threshold",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum stock level before reordering'})
    )
    
    unit_price = forms.DecimalField(
        required=True,
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label="Unit Price (SGD)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price in SGD', 'step': '0.01'})
    )
    
    product_rating = forms.DecimalField(
        required=True,
        max_digits=3,
        decimal_places=1,
        min_value=Decimal('0.0'),
        max_value=Decimal('5.0'),
        label="Product Rating (0-5)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rating from 0.0 to 5.0', 'step': '0.1'})
    )
    
    class Meta:
        model = Product
        fields = ['sku_code', 'product_name', 'product_description', 'product_category', 
                  'quantity_on_hand', 'reorder_quantity', 'unit_price', 'product_rating']
    
    def clean_sku_code(self):
        sku = self.cleaned_data.get('sku_code', '').strip().upper()
        if not sku:
            raise ValidationError("SKU code is required.")
        if len(sku) < 3:
            raise ValidationError("SKU code must be at least 3 characters long.")
        
        if self.instance.pk:
            if Product.objects.filter(sku_code=sku).exclude(pk=self.instance.pk).exists():
                raise ValidationError("A product with this SKU code already exists.")
        else:
            if Product.objects.filter(sku_code=sku).exists():
                raise ValidationError("A product with this SKU code already exists.")
        
        return sku
    
    def clean_product_name(self):
        name = self.cleaned_data.get('product_name', '').strip()
        if not name:
            raise ValidationError("Product name is required.")
        if len(name) < 3:
            raise ValidationError("Product name must be at least 3 characters long.")
        return name
    
    def clean_product_description(self):
        description = self.cleaned_data.get('product_description', '').strip()
        if not description:
            raise ValidationError("Product description is required.")
        if len(description) < 10:
            raise ValidationError("Product description must be at least 10 characters long.")
        return description
    
    def clean_product_category(self):
        category = self.cleaned_data.get('product_category')
        if not category:
            raise ValidationError("Please select a category.")
        return category
    
    def clean_quantity_on_hand(self):
        quantity = self.cleaned_data.get('quantity_on_hand')
        if quantity is None:
            raise ValidationError("Stock quantity is required.")
        if quantity < 0:
            raise ValidationError("Stock quantity cannot be negative.")
        return quantity
    
    def clean_reorder_quantity(self):
        reorder = self.cleaned_data.get('reorder_quantity')
        if reorder is None:
            raise ValidationError("Reorder threshold is required.")
        if reorder < 0:
            raise ValidationError("Reorder threshold cannot be negative.")
        return reorder
    
    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is None:
            raise ValidationError("Unit price is required.")
        if price <= 0:
            raise ValidationError("Unit price must be greater than 0.")
        if price > Decimal('999999.99'):
            raise ValidationError("Unit price is too high.")
        return price
    
    def clean_product_rating(self):
        rating = self.cleaned_data.get('product_rating')
        if rating is None:
            raise ValidationError("Product rating is required.")
        if rating < Decimal('0.0') or rating > Decimal('5.0'):
            raise ValidationError("Product rating must be between 0.0 and 5.0.")
        return rating


class StockAdjustmentForm(forms.Form):
    quantity_on_hand = forms.IntegerField(
        required=True,
        min_value=0,
        label="Stock Quantity",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter new stock quantity'})
    )
    
    def clean_quantity_on_hand(self):
        quantity = self.cleaned_data.get('quantity_on_hand')
        if quantity is None:
            raise ValidationError("Stock quantity is required.")
        if quantity < 0:
            raise ValidationError("Stock quantity cannot be negative.")
        return quantity


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        required=True,
        label="CSV File",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
    
    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if file:
            if not file.name.endswith('.csv'):
                raise ValidationError("File must be a CSV file.")
            if file.size > 5242880:
                raise ValidationError("File size must be less than 5MB.")
        return file


class BulkPriceUpdateForm(forms.Form):
    CATEGORY_CHOICES = [
        ('', 'Select Category'),
        ('Electronics', 'Electronics'),
        ('Fashion - Men', 'Fashion - Men'),
        ('Fashion - Women', 'Fashion - Women'),
        ('Home & Garden', 'Home & Garden'),
        ('Beauty & Personal Care', 'Beauty & Personal Care'),
        ('Sports & Outdoors', 'Sports & Outdoors'),
        ('Toys & Games', 'Toys & Games'),
        ('Books & Media', 'Books & Media'),
        ('Health & Wellness', 'Health & Wellness'),
        ('Automotive', 'Automotive'),
    ]
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=True,
        label="Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    percentage = forms.DecimalField(
        required=True,
        max_digits=5,
        decimal_places=2,
        label="Percentage Change",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter percentage (e.g., 10 for +10%, -15 for -15%)', 'step': '0.01'})
    )
    
    def clean_category(self):
        category = self.cleaned_data.get('category')
        if not category:
            raise ValidationError("Please select a category.")
        return category
    
    def clean_percentage(self):
        percentage = self.cleaned_data.get('percentage')
        if percentage is None:
            raise ValidationError("Percentage is required.")
        if percentage < -100:
            raise ValidationError("Percentage cannot be less than -100%.")
        if percentage > 1000:
            raise ValidationError("Percentage cannot exceed 1000%.")
        if percentage == 0:
            raise ValidationError("Percentage cannot be zero.")
        return percentage


class StaffUserForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'})
    )
    
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'staff@auroramart.com'})
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    
    password = forms.CharField(
        required=True,
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )
    
    def clean_username(self):
        from django.contrib.auth.models import User
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise ValidationError("Username is required.")
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username
    
    def clean_email(self):
        from django.contrib.auth.models import User
        email = self.cleaned_data.get('email', '').lower().strip()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            raise ValidationError("Password is required.")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return password


class CustomerForm(forms.ModelForm):
    age = forms.IntegerField(
        required=True,
        min_value=18,
        max_value=120,
        label="Age",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    GENDER_CHOICES = [
        ('', 'Select Gender'),
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=True,
        label="Gender",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    EMPLOYMENT_CHOICES = [
        ('', 'Select Employment Status'),
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Self-employed', 'Self-employed'),
        ('Student', 'Student'),
        ('Retired', 'Retired'),
        ('Unemployed', 'Unemployed'),
    ]
    employment_status = forms.ChoiceField(
        choices=EMPLOYMENT_CHOICES,
        required=True,
        label="Employment Status",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    OCCUPATION_CHOICES = [
        ('', 'Select Occupation'),
        ('Tech', 'Technology'),
        ('Sales', 'Sales'),
        ('Service', 'Service'),
        ('Admin', 'Administration'),
        ('Education', 'Education'),
        ('Skilled Trades', 'Skilled Trades'),
        ('Healthcare', 'Healthcare'),
        ('Other', 'Other'),
    ]
    occupation = forms.ChoiceField(
        choices=OCCUPATION_CHOICES,
        required=True,
        label="Occupation",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    EDUCATION_CHOICES = [
        ('', 'Select Education Level'),
        ('Secondary', 'Secondary'),
        ('Diploma', 'Diploma'),
        ('Bachelor', 'Bachelor'),
        ('Master', 'Master'),
        ('Doctorate', 'Doctorate'),
    ]
    education = forms.ChoiceField(
        choices=EDUCATION_CHOICES,
        required=True,
        label="Education Level",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    household_size = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=15,
        label="Household Size",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    has_children = forms.BooleanField(
        required=False,
        label="Has Children",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    monthly_income_sgd = forms.DecimalField(
        required=True,
        max_digits=12,
        decimal_places=2,
        min_value=0,
        label="Monthly Income (SGD)",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Customer
        fields = ['age', 'gender', 'employment_status', 'occupation', 'education', 
                  'household_size', 'has_children', 'monthly_income_sgd']
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise ValidationError("Age is required.")
        if age < 18:
            raise ValidationError("Customer must be at least 18 years old.")
        if age > 120:
            raise ValidationError("Please enter a valid age.")
        return age
    
    def clean_household_size(self):
        size = self.cleaned_data.get('household_size')
        if size is None:
            raise ValidationError("Household size is required.")
        if size < 1:
            raise ValidationError("Household size must be at least 1.")
        if size > 15:
            raise ValidationError("Please enter a valid household size.")
        return size
    
    def clean_monthly_income_sgd(self):
        income = self.cleaned_data.get('monthly_income_sgd')
        if income is None:
            raise ValidationError("Monthly income is required.")
        if income < 0:
            raise ValidationError("Monthly income cannot be negative.")
        if income > 1000000:
            raise ValidationError("Please enter a valid monthly income.")
        return income
