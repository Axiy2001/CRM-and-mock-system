from django import forms

from .models import User


class StudentCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.TextInput(attrs={
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()

        return user


class MockCreatorCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.TextInput(attrs={
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'mock_creator'
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()

        return user

class AssistantAdminCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.TextInput(attrs={
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'assistant_admin'
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()

        return user