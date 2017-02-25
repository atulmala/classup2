from django.db import models
from setup.models import School

# Create your models here.


# Create your models here.
class Teacher(models.Model):
    teacher_erp_id = models.CharField(max_length=30)    # this can be the existing employee id of the teacher
    school = models.ForeignKey(School)
    first_name = models.CharField(max_length=50, blank=False, null=False)
    last_name = models.CharField(max_length=50, null=False)
    email = models.EmailField(default='defaultemail@classup.in')     # email will also be used as login id
    mobile = models.CharField(max_length=20, blank=False, null=True)
    active_status = models.BooleanField(default=True)

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name
