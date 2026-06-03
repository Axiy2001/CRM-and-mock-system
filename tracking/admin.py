from django.contrib import admin
from .models import Attendance
from .models import Attendance, Homework, HomeworkStatus

# Register your models here.



@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'classroom', 'date', 'status', 'marked_by')
    list_filter = ('status', 'date', 'classroom')
    search_fields = ('student__username', 'classroom__name')

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'due_date', 'created_by', 'created_at')
    list_filter = ('classroom', 'due_date')
    search_fields = ('title', 'classroom__name')


@admin.register(HomeworkStatus)
class HomeworkStatusAdmin(admin.ModelAdmin):
    list_display = ('student', 'homework', 'status', 'score', 'checked_by', 'checked_at')
    list_filter = ('status', 'checked_at')
    search_fields = ('student__username', 'homework__title', 'comment')