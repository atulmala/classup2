from django.db import models
from setup.models import School
from student.models import Student


# Create your models here.

class CollectAdmFee(models.Model):
    school = models.ForeignKey(School)
    student = models.ForeignKey(Student)

    def __unicode__(self):
        return '%s %s' % (self.school, self.student)


class FeePaymentHistory(models.Model):
    school = models.ForeignKey(School)
    student = models.ForeignKey(Student)
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=7)
    mode = models.CharField(max_length=50)
    comments = models.CharField(max_length=100)


class PreviousBalance(models.Model):
    school = models.ForeignKey(School)
    student = models.ForeignKey(Student)
    due_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=7)
    negative = models.BooleanField(default=True)

