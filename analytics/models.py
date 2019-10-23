from django.db import models
from student.models import Student
from academics.models import Subject, Exam

# Create your models here.


class SubjectAnalysis(models.Model):
    student = models.ForeignKey(Student)
    exam = models.ForeignKey(Exam)
    subject = models.ForeignKey(Subject)
    marks = models.DecimalField(max_digits=6, decimal_places=2)
    highest = models.DecimalField(max_digits=6, decimal_places=2)
    average = models.DecimalField(max_digits=6, decimal_places=2)

