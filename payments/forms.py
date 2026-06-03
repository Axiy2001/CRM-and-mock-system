from datetime import datetime

from django import forms

from accounts.models import User
from academics.models import ClassRoom, StudentClass
from .models import Payment


class PaymentCreateForm(forms.ModelForm):
    month = forms.CharField(
        widget=forms.TextInput(attrs={
            'type': 'month'
        })
    )

    paid_amount = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'money-input',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = Payment
        fields = [
            'student',
            'classroom',
            'month',
            'month_lessons',
            'student_lessons',
            'paid_amount',
            'comment',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.role == 'assistant_admin':
            classrooms = ClassRoom.objects.filter(
                assistant_admin=user
            )
        else:
            classrooms = ClassRoom.objects.all()

        self.fields['classroom'].queryset = classrooms

        student_ids = StudentClass.objects.filter(
            classroom__in=classrooms,
            is_active=True
        ).values_list('student_id', flat=True)

        self.fields['student'].queryset = User.objects.filter(
            id__in=student_ids,
            role='student'
        )

    def clean_month(self):
        month_value = self.cleaned_data['month']
        return datetime.strptime(month_value, '%Y-%m').date()

    def clean_paid_amount(self):
        paid_amount = self.cleaned_data['paid_amount']
        paid_amount = paid_amount.replace(' ', '')

        if not paid_amount.isdigit():
            raise forms.ValidationError('Faqat raqam kiriting.')

        return int(paid_amount)

    def clean(self):
        cleaned_data = super().clean()

        month_lessons = cleaned_data.get('month_lessons')
        student_lessons = cleaned_data.get('student_lessons')

        if month_lessons is not None and month_lessons <= 0:
            self.add_error('month_lessons', 'Bu oy darslar soni 0 dan katta bo‘lishi kerak.')

        if student_lessons is not None and student_lessons < 0:
            self.add_error('student_lessons', 'Student darslar soni manfiy bo‘lmasligi kerak.')

        if month_lessons and student_lessons and student_lessons > month_lessons:
            self.add_error('student_lessons', 'Student darslari oy darslaridan ko‘p bo‘lmasligi kerak.')

        return cleaned_data