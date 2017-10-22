from django.db import models

from student.models import Student

# Create your models here.


class ParentCommunicationCategories(models.Model):
    category = models.CharField(max_length=100)

    def __unicode__(self):
        return self.category


class ParentCommunication(models.Model):
    student = models.ForeignKey(Student)
    date_sent = models.DateField()
    category = models.ForeignKey(ParentCommunicationCategories)
    communication_text = models.CharField(max_length=400)

    def __unicode__(self):
        return self.student.fist_name + ' ' + self.student.last_name

