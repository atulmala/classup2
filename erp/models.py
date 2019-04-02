from django.db import models
from setup.models import School
from student.models import Student, Parent


# Create your models here.

class ReceiptNumber(models.Model):
    school = models.ForeignKey(School)
    start_receipt = models.IntegerField(default=1000)


class CollectAdmFee(models.Model):
    school = models.ForeignKey(School)
    student = models.ForeignKey(Student)

    def __unicode__(self):
        return '%s %s' % (self.school, self.student)


class FeePaymentHistory(models.Model):
    school = models.ForeignKey(School)
    student = models.ForeignKey(Student)
    parent = models.ForeignKey(Parent, null=True)
    date = models.DateField(auto_now_add=True)
    previous_due = models.DecimalField(default=0.0, decimal_places=2, max_digits=7)
    amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=7)
    fine = models.DecimalField(default=0.0, decimal_places=2, max_digits=7)
    discount = models.DecimalField(default=0.0, decimal_places=2, max_digits=7)
    mode = models.CharField(max_length=50)
    comments = models.CharField(max_length=100)
    cheque_number = models.CharField(max_length=6, default='N/A')
    bank = models.CharField(max_length=20, default='N/A')
    receipt_number = models.IntegerField()

    # we will extract parent from student
    def save(self, *args, **kwargs):
        p = self.student.parent
        self.parent = p
        super(FeePaymentHistory, self).save(*args, **kwargs)

    def __unicode__(self):
        return str(self.receipt_number)


class PreviousBalance(models.Model):
    school = models.ForeignKey(School)
    student = models.ForeignKey(Student)
    parent = models.ForeignKey(Parent, null=True)
    due_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=7)
    negative = models.BooleanField(default=True)

    # we will extract parent from student
    def save(self, *args, **kwargs):
        p = self.student.parent
        self.parent = p
        super(PreviousBalance, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%s %s' % (self.student.fist_name, self.student.last_name)


class PrevBalStudent(models.Model):
    school = models.ForeignKey(School)
    student = models.ForeignKey(Student)
    parent = models.ForeignKey(Parent, null=True)
    due_amount = models.DecimalField(default=0.0, decimal_places=2, max_digits=7)
    negative = models.BooleanField(default=True)


class HeadWiseFee(models.Model):
    date = models.DateField(auto_now_add=True)
    PaymentHistory = models.ForeignKey(FeePaymentHistory)
    school = models.ForeignKey(School)
    student = models.ForeignKey(Student)
    head = models.CharField(max_length=20)
    amount = models.DecimalField(decimal_places=2, max_digits=7)

