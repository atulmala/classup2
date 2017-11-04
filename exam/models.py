from django.db import models

from setup.models import School
from academics.models import Class, Subject

# Create your models here.


class Scheme(models.Model):
    school = models.ForeignKey(School)
    the_class = models.ForeignKey(Class)
    sequence = models.IntegerField()
    subject = models.ForeignKey(Subject)
