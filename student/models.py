from django.db import models
from setup.models import School

# Create your models here.


class Parent(models.Model):
    parent_name = models.CharField(max_length=100)
    parent_mobile1 = models.CharField(max_length=20)
    parent_mobile2 = models.CharField(max_length=20, null=True, blank=True)
    parent_email = models.EmailField(blank=True, null=True)

    def __unicode__(self):
        return self.parent_name

    def get_name(self):
        return self.parent_name


class Student(models.Model):
    student_erp_id = models.CharField(max_length=30, null=True,
                                      blank=True, db_column='student_erp_id') # this can be existing id such as registration number
    school = models.ForeignKey(School)
    fist_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    roll_number = models.IntegerField()
    current_class = models.ForeignKey('academics.Class')
    current_section = models.ForeignKey('academics.Section')
    parent = models.ForeignKey(Parent, default=None)
    active_status = models.BooleanField(default=True)

    class Meta:
        ordering = ('fist_name', )

    def __unicode__(self):
        return '%s %s' % (self.fist_name, self.last_name)


class DOB(models.Model):
    student = models.ForeignKey(Student)
    dob = models.DateField()


class AdditionalDetails(models.Model):
    student = models.ForeignKey(Student)
    mother_name = models.CharField(max_length=50, default='Not Available')
    address = models.CharField(max_length=200, default=' ')
    adhar = models.CharField(max_length=30, default='Not Available')
    blood_group = models.CharField(max_length=10, default='Not Available')
    father_occupation = models.CharField(max_length=100, default='Not Available')
    mother_occupation = models.CharField(max_length=100, default='Not Available')

