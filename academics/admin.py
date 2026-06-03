from django.contrib import admin
from .models import ClassRoom, StudentClass


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'teacher', 'assistant_admin', 'created_at')
    search_fields = ('name', 'subject')
    list_filter = ('subject', 'teacher', 'assistant_admin', 'created_at')


@admin.register(StudentClass)
class StudentClassAdmin(admin.ModelAdmin):
    list_display = ('student', 'classroom', 'is_active', 'joined_at')
    list_filter = ('classroom', 'is_active')
    search_fields = ('student__username', 'classroom__name')