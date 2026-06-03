from django.contrib import admin

# Register your models here.

from .models import (
    MockTest,
    ReadingPassage,
    Question,
    Choice,
    MockAccess,
    MockResult,
)


admin.site.register(MockTest)
admin.site.register(ReadingPassage)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(MockAccess)
admin.site.register(MockResult)