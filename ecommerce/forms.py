from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Customer

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
        # Add bootstrap classes to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

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