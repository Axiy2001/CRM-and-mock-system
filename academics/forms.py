from django import forms
from django.contrib.auth import get_user_model

from .models import ClassRoom

User = get_user_model()


class ClassRoomCreateForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = [
            'name',
            'subject',
            'monthly_price',
            'assistant_admin',
        ]

        widgets = {
            'monthly_price': forms.NumberInput(attrs={
                'placeholder': '350000'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['assistant_admin'].queryset = User.objects.filter(
            role='assistant_admin',
            is_active=True
        )


class AssignTeacherForm(forms.Form):
    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role='teacher',
            is_active=True
        ),
        required=False,
        label='Teacher'
    )


class AddStudentToClassForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role='student',
            is_active=True
        ),
        label='Student'
    )


class AssignAssistantAdminForm(forms.ModelForm):
    assistant_admin = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role='assistant_admin',
            is_active=True
        ),
        required=False,
        label='Assistant Admin'
    )

    class Meta:
        model = ClassRoom
        fields = ['assistant_admin']