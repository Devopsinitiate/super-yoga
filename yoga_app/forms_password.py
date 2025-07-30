from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .forms import TAILWIND_INPUT_CLASSES

class TailwindPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.PasswordInput,)):
                field.widget.attrs['class'] = TAILWIND_INPUT_CLASSES
                if field_name == 'old_password':
                    field.widget.attrs['placeholder'] = 'Enter your current password'
                elif field_name == 'new_password1':
                    field.widget.attrs['placeholder'] = 'Enter your new password'
                elif field_name == 'new_password2':
                    field.widget.attrs['placeholder'] = 'Confirm your new password'
