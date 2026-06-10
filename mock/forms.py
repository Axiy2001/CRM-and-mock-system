from django import forms

from .models import (
    MockTest,
    ReadingPart,
    ReadingPassage,
    Question,
)


class MockTestCreateForm(forms.ModelForm):
    class Meta:
        model = MockTest
        fields = [
            'title',
            'mock_type',
            'description',
            'duration_minutes',
        ]


class ReadingPartCreateForm(forms.ModelForm):
    class Meta:
        model = ReadingPart
        fields = [
            'title',
            'instruction',
            'order',
        ]

        widgets = {
            'instruction': forms.Textarea(attrs={
                'rows': 5
            })
        }


class ReadingPassageCreateForm(forms.ModelForm):
    class Meta:
        model = ReadingPassage
        fields = [
            'title',
            'content',
            'order',
        ]

        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 12
            })
        }


class QuestionCreateForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'question_text',
            'correct_answer',
            'order',
        ]

        widgets = {
            'question_text': forms.Textarea(attrs={
                'rows': 4
            })
        }