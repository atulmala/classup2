from django.db import models

# Create your models here.
from academics.models import Class, Subject, Exam
from setup.models import School
from student.models import Student
from teacher.models import Teacher


class OnlineTest(models.Model):
    school = models.ForeignKey(School, null=True)
    exam = models.ForeignKey(Exam, null=True)
    the_class = models.ForeignKey(Class)
    subject = models.ForeignKey(Subject)
    teacher = models.ForeignKey(Teacher)
    date = models.DateField()
    duration = models.IntegerField(default=30)


class OnlineQuestion(models.Model):
    test = models.ForeignKey(OnlineTest)
    question = models.CharField(max_length=400)
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=5)


class StudentQuestion(models.Model):
    student = models.ForeignKey(Student)
    question = models.ForeignKey(OnlineQuestion)
    answer_marked = models.CharField(max_length=5)
    whether_correct = models.BooleanField(default=False)


class StudentTestAttempt(models.Model):
    student = models.ForeignKey(Student)
    online_test = models.ForeignKey(OnlineTest)
    date = models.DateTimeField(auto_now_add=True)
    submission_ok = models.BooleanField(default=True)


class AnswerSheets(models.Model):
    student = models.ForeignKey(Student)
    online_test = models.ForeignKey(OnlineTest)
    link = models.CharField(max_length=200)
    shared = models.BooleanField(default=False)
