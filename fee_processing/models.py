from django.db import models

# Create your models here.
from student.models import Student


class FeeDefaulters(models.Model):
    student = models.ForeignKey(Student)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    stop_access = models.BooleanField(default=False)