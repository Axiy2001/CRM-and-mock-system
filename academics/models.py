from django.db import models
from django.conf import settings


class ClassRoom(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100, blank=True, null=True)
    monthly_price = models.PositiveIntegerField(default=0)

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'teacher'},
        related_name='classes'
    )

    assistant_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'assistant_admin'},
        related_name='managed_classes'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class StudentClass(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='student_classes'
    )

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name='students'
    )

    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='removed_student_classes'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'classroom'],
                condition=models.Q(is_active=True),
                name='unique_active_student_per_class'
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.classroom}"
