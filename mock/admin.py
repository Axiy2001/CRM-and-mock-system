from django.contrib import admin

from .models import (
    MockTest,
    ReadingPart,
    ReadingPassage,
    Question,
    Choice,
    ListeningPart,
    ListeningQuestion,
    ListeningQuestionChoice,
    MockAccess,
    MockResult,
)


admin.site.register(MockTest)
admin.site.register(ReadingPart)
admin.site.register(ReadingPassage)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(ListeningPart)
admin.site.register(ListeningQuestion)
admin.site.register(ListeningQuestionChoice)
admin.site.register(MockAccess)
admin.site.register(MockResult)