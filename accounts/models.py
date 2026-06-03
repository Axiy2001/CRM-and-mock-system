from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('assistant_admin', 'Assistant Admin'),
        ('mock_creator', 'Mock Creator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )

    deactivated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    deactivated_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deactivated_users'
    )

    def __str__(self):
        return f"{self.username} - {self.role}"