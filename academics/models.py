from django.db import models


# Create your models here.

from setup.models import School
from student.models import Student
from teacher.models import Teacher


class Section(models.Model):
    school = models.ForeignKey(School)
    section = models.CharField(max_length=5)

    def __unicode__(self):
        return self.section
        # return self.school.school_name + ', ' + self.section


class Class(models.Model):
    school = models.ForeignKey(School)
    standard = models.CharField(max_length=20)
    sequence = models.SmallIntegerField()

    def __unicode__(self):
        # return self.school.school_name + ', ' + str(self.standard)
        return self.standard


class ClassTeacher(models.Model):
    school = models.ForeignKey(School)
    standard = models.ForeignKey(Class)
    section = models.ForeignKey(Section)
    class_teacher = models.ForeignKey(Teacher)

    def __unicode__(self):
        return self.school.school_name + ', ' + self.standard.standard + ' ' + self.section.section + ' ' + \
               self.class_teacher.first_name + ' ' + self.class_teacher.last_name


class Subject(models.Model):
    school = models.ForeignKey(School)
    subject_name = models.CharField(max_length=40)
    subject_code = models.CharField(max_length=10)
    subject_sequence = models.SmallIntegerField(null=True)

    def __unicode__(self):
        return self.subject_name


class ClassTest(models.Model):
    date_conducted = models.DateField()
    teacher = models.ForeignKey(Teacher)
    subject = models.ForeignKey(Subject)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2)
    passing_marks = models.DecimalField(max_digits=6, decimal_places=2)
    grade_based = models.BooleanField()
    is_completed = models.BooleanField(default=False)
    test_type = models.CharField(max_length=200, default='unit')
    syllabus = models.CharField(max_length=200, default=" ")

    def __unicode__(self):
        return self.the_class.standard + ' ' + self.section.section + ' ' \
               + self.subject.subject_name + ' ' + (self.date_conducted).strftime('%d/%m/%Y')


class TestResults(models.Model):
    class_test = models.ForeignKey(ClassTest)
    student = models.ForeignKey(Student, db_column='student_erp_id')
    roll_no = models.IntegerField(null=True)
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    grade = models.CharField(max_length=15, null=True)

    def __unicode__(self):
        return self.student.fist_name + ' ' + self.student.last_name + ' ' + \
               self.class_test.the_class.standard + ' ' + self.class_test.section.section + ' ' \
               + self.class_test.subject.subject_name + ' ' + (self.class_test.date_conducted).strftime('%d/%m/%Y')


    

class Term(models.Model):
    term = models.CharField(max_length=10, default='Term 1')
    def __unicode__(self):
        return self.term
    
    
class TermTestResult(models.Model):
    # 21/09/2017 for CBSE evaluation. Below fields will be applicable only if the test is Term Test
    test_result = models.ForeignKey(TestResults)
    periodic_test_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    note_book_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    sub_enrich_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)


class Grade(models.Model):
    grade = models.CharField(max_length=4)
    
    def __unicode__(self):
        return self.grade


class CoScholastics(models.Model):
    term = models.CharField(max_length=10)
    the_class = models.ForeignKey(Class, null=True)
    section = models.ForeignKey(Section, null=True)
    student = models.ForeignKey(Student)
    work_education = models.CharField(max_length=4, default=' ', blank=True)
    art_education = models.CharField(max_length=4, default=' ', blank=True)
    health_education = models.CharField(max_length=4, default=' ', blank=True)
    discipline = models.CharField(max_length=4, default=' ', blank=True)
    teacher_remarks = models.CharField(max_length=100, default='All the Best')
    promoted_to_class = models.CharField(max_length=10, default=' ', blank='True')
    




class Exam(models.Model):
    school = models.ForeignKey(School)
    title = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    start_class = models.CharField(max_length=20, null=True)
    start_class_sequence = models.SmallIntegerField(null=True)
    end_class = models.CharField(max_length=20, null=True)
    end_class_sequence = models.SmallIntegerField(null=True)

    # what is provide in the data is the standard. We need to extract the sequence of the class
    def save(self, *args, **kwargs):
        sc = Class.objects.get(school=self.school, standard=self.start_class)
        self.start_class_sequence = sc.sequence
        ec = Class.objects.get(school=self.school, standard=self.end_class)
        self.end_class_sequence = ec.sequence
        super(Exam, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title + \
               ' start date: ' + self.start_date.strftime('%d/%m/%Y') + \
               ', end date: ' + self.end_date.strftime('%d/%m/%Y') + \
               ', from class: ' + self.start_class + ' - ' + self.end_class


class TeacherSubjects(models.Model):
    teacher = models.ForeignKey(Teacher)
    subject = models.ForeignKey(Subject)

    def __unicode__(self):
        return self.teacher.first_name + ' ' + self.teacher.last_name + ' ' + self.subject.subject_name


class WorkingDays(models.Model):
    school = models.ForeignKey(School)
    year = models.SmallIntegerField()
    month = models.SmallIntegerField()
    working_days = models.SmallIntegerField()

    def __unicode__(self):
        return str(self.year) + '/' + str(self.month)


class HomeWork(models.Model):
    teacher = models.ForeignKey(Teacher)
    the_class = models.ForeignKey(Class)
    section = models.ForeignKey(Section)
    subject = models.ForeignKey(Subject)
    creation_date = models.DateTimeField(null=True, auto_now_add=True)
    due_date = models.DateField()
    notes = models.CharField(max_length=200)
    location = models.ImageField(upload_to='homework/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class HW(models.Model):
    school = models.ForeignKey(School, null=True)
    teacher = models.CharField(max_length=50)
    the_class = models.CharField(max_length=10)
    section = models.CharField(max_length=10)
    subject = models.CharField(max_length=100)
    creation_date = models.DateTimeField(null=True, auto_now_add=True)
    due_date = models.DateField()
    notes = models.CharField(max_length=200, default='No comments')
    location = models.ImageField(upload_to='homework/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def image_tag(self):
        return u'<img src="/homework/%s" width="150" height="150" />' % (self.image)

    image_tag.short_description = 'Image'
    image_tag.allow_tags = True




