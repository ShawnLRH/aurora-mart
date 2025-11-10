from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Customer
import re

class SignUpForm(UserCreationForm):
    # User fields
    full_name = forms.CharField(
        max_length=100, 
        required=True, 
        label="Full Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'})
    )
    email = forms.EmailField(
        required=True, 
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'})
    )
    
    # Customer demographic fields
    age = forms.IntegerField(
        required=True,
        min_value=18,
        max_value=120,
        label="Age",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter your age'})
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
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of people in household'})
    )
    
    has_children = forms.BooleanField(
        required=False,
        label="Do you have children?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    monthly_income_sgd = forms.DecimalField(
        required=True,
        max_digits=12,
        decimal_places=2,
        min_value=0,
        label="Monthly Income (SGD)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter monthly income in SGD'})
    )

    class Meta:
        model = User
        fields = ('full_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add bootstrap classes and help text to password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Enter password',
            'minlength': '8'
        })
        self.fields['password1'].help_text = (
            '<small class="form-text text-muted">'
            'Password must be at least 8 characters and contain:<br>'
            '• At least one uppercase letter (A-Z)<br>'
            '• At least one lowercase letter (a-z)<br>'
            '• At least one number (0-9)<br>'
            '• At least one special character (!@#$%^&*)'
            '</small>'
        )
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control', 
            'placeholder': 'Confirm password'
        })
        self.fields['password2'].help_text = '<small class="form-text text-muted">Enter the same password again for verification.</small>'

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if not full_name:
            raise ValidationError("Full name is required.")
        if len(full_name) < 2:
            raise ValidationError("Full name must be at least 2 characters long.")
        if not re.match(r'^[a-zA-Z\s\'-]+$', full_name):
            raise ValidationError("Full name can only contain letters, spaces, hyphens, and apostrophes.")
        return full_name
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if not email:
            raise ValidationError("Email is required.")
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists. Please use a different email or login.")
        if User.objects.filter(username=email).exists():
            raise ValidationError("An account with this email already exists. Please use a different email or login.")
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if not password:
            raise ValidationError("Password is required.")
        
        # Minimum length check
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter (A-Z).")
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter (a-z).")
        
        # Check for digit
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number (0-9).")
        
        # Check for special character
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            raise ValidationError("Password must contain at least one special character (!@#$%^&* etc.).")
        
        return password
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise ValidationError("Age is required.")
        if age < 18:
            raise ValidationError("You must be at least 18 years old to create an account.")
        if age > 120:
            raise ValidationError("Please enter a valid age.")
        return age
    
    def clean_gender(self):
        gender = self.cleaned_data.get('gender')
        if not gender:
            raise ValidationError("Please select your gender.")
        return gender
    
    def clean_employment_status(self):
        employment_status = self.cleaned_data.get('employment_status')
        if not employment_status:
            raise ValidationError("Please select your employment status.")
        return employment_status
    
    def clean_occupation(self):
        occupation = self.cleaned_data.get('occupation')
        if not occupation:
            raise ValidationError("Please select your occupation.")
        return occupation
    
    def clean_education(self):
        education = self.cleaned_data.get('education')
        if not education:
            raise ValidationError("Please select your education level.")
        return education
    
    def clean_household_size(self):
        household_size = self.cleaned_data.get('household_size')
        if household_size is None:
            raise ValidationError("Household size is required.")
        if household_size < 1:
            raise ValidationError("Household size must be at least 1.")
        if household_size > 15:
            raise ValidationError("Please enter a valid household size (maximum 15).")
        return household_size
    
    def clean_monthly_income_sgd(self):
        income = self.cleaned_data.get('monthly_income_sgd')
        if income is None:
            raise ValidationError("Monthly income is required.")
        if income < 0:
            raise ValidationError("Monthly income cannot be negative.")
        if income > 1000000:
            raise ValidationError("Please enter a valid monthly income.")
        return income

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name_parts = self.cleaned_data['full_name'].split()
        user.first_name = full_name_parts[0]
        if len(full_name_parts) > 1:
            user.last_name = ' '.join(full_name_parts[1:])
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Create associated Customer profile
            Customer.objects.create(
                user=user,
                age=self.cleaned_data['age'],
                gender=self.cleaned_data['gender'],
                employment_status=self.cleaned_data['employment_status'],
                occupation=self.cleaned_data['occupation'],
                education=self.cleaned_data['education'],
                household_size=self.cleaned_data['household_size'],
                has_children=self.cleaned_data['has_children'],
                monthly_income_sgd=self.cleaned_data['monthly_income_sgd'],
                preferred_category=''  # Will be predicted later by AI
            )
        return user


class SupportTicketForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        required=True,
        label="Your Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'})
    )
    
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'})
    )
    
    subject = forms.CharField(
        max_length=200,
        required=True,
        label="Subject",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description of your issue'})
    )
    
    message = forms.CharField(
        required=True,
        label="Message",
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'placeholder': 'Please describe your issue in detail...',
            'rows': 6
        })
    )
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError("Name is required.")
        if len(name) < 2:
            raise ValidationError("Name must be at least 2 characters long.")
        return name
    
    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if not subject:
            raise ValidationError("Subject is required.")
        if len(subject) < 5:
            raise ValidationError("Subject must be at least 5 characters long.")
        return subject
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise ValidationError("Message is required.")
        if len(message) < 20:
            raise ValidationError("Please provide more details. Message must be at least 20 characters long.")
        return message