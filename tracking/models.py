from django.db import models
from django.conf import settings

from academics.models import ClassRoom


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='attendances'
    )
    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    late_time = models.TimeField(null=True, blank=True)

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'classroom', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.username} - {self.classroom.name} - {self.date} - {self.status}"


class Homework(models.Model):
    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name='homeworks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_homeworks'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} - {self.classroom.name}"


class HomeworkStatus(models.Model):
    STATUS_CHOICES = (
        ('done', 'Done'),
        ('not_done', 'Not Done'),
        ('partial', 'Partial'),
    )

    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='statuses'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='homework_statuses'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    score = models.PositiveIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True, null=True)

    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_homeworks'
    )

    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('homework', 'student')
        ordering = ['-checked_at']

    def __str__(self):
        return f"{self.student.username} - {self.homework.title} - {self.status}"