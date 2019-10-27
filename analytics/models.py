from django.db import models
from student.models import Student
from academics.models import Class, Section, Subject, Exam

# Create your models here.


class ExamHighestAverage(models.Model):
    exam = models.ForeignKey(Exam)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)
    highest = models.DecimalField(max_digits=6, decimal_places=2)
    average = models.DecimalField(max_digits=6, decimal_places=2)


class SubjectHighestAverage(models.Model):
    exam = models.ForeignKey(Exam)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)
    subject = models.ForeignKey(Subject)
    highest = models.DecimalField(max_digits=6, decimal_places=2)
    average = models.DecimalField(max_digits=6, decimal_places=2)


class SubjectAnalysis(models.Model):
    student = models.ForeignKey(Student)
    exam = models.ForeignKey(Exam)
    subject = models.ForeignKey(Subject)
    marks = models.DecimalField(max_digits=6, decimal_places=2)
    highest = models.DecimalField(max_digits=6, decimal_places=2)
    average = models.DecimalField(max_digits=6, decimal_places=2)

