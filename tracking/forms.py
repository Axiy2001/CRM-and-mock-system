from django import forms
from .models import Homework


class HomeworkCreateForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['classroom', 'title', 'description', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if teacher:
            self.fields['classroom'].queryset = teacher.classes.all()