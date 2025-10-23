from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True, label="Full Name")
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ('full_name', 'email', 'password1', 'password2')

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
        return user