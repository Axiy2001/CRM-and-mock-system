from django.db import models
from django.conf import settings

from academics.models import ClassRoom


# Create your models here.





class Payment(models.Model):
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('unpaid', 'Unpaid'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='payments'
    )

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    month = models.DateField()

    month_lessons = models.PositiveIntegerField(default=0)
    student_lessons = models.PositiveIntegerField(default=0)

    amount = models.PositiveIntegerField(default=0)
    paid_amount = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unpaid'
    )

    comment = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_payments'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'classroom', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"{self.student.username} - {self.classroom.name} - {self.month}"

    @property
    def debt(self):
        return self.amount - self.paid_amount