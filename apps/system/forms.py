from django import forms
from apps.system.models import Contact


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name','email', 'subject', 'message', 'honeypot']
        widgets = {
            'honeypot': forms.HiddenInput,
        }
