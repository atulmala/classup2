from django.shortcuts import render

# Create your views here.

import os
import mimetypes
import json
import base64
import datetime
from datetime import date

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle


from django.core.files.base import ContentFile
from django.core.servers.basehttp import FileWrapper
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.test import RequestFactory

from authentication.views import JSONResponse, log_entry
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics
import Queue

from attendance.models import Attendance, AttendanceTaken
from teacher.models import Teacher
from student.models import Student, DOB
from setup.models import Configurations, School
from .models import Class, Section, Subject, ClassTest, TestResults, Exam, HW, TermTestResult, CoScholastics
from .serializers import ClassSerializer, SectionSerializer, \
    SubjectSerializer, TestSerializer, ClassSectionForTestSerializer, \
    TestMarksSerializer, TestTypeSerializer, ExamSerializer, HWSerializer, CoScholasticSerializer

from operations import sms


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class ClassList(generics.ListCreateAPIView):
    serializer_class = ClassSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        q = Class.objects.filter(school=school).order_by('sequence')
        return q


class SectionList(generics.ListCreateAPIView):
    serializer_class = SectionSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        q = Section.objects.filter(school=school)
        return q


class SubjectList(generics.ListCreateAPIView):
    serializer_class = SubjectSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        q = Subject.objects.filter(school=school).order_by('subject_sequence')
        return q


class ExamList(generics.ListCreateAPIView):
    serializer_class = ExamSerializer

    def get_queryset(self):
        student_id = self.kwargs['student_id']
        student = Student.objects.get(id=student_id)
        school = student.school
        the_class = student.current_class
        class_sequence = the_class.sequence
        q = Exam.objects.filter(school=school, start_class_sequence__lte=class_sequence,
                                end_class_sequence__gte=class_sequence)

        try:
            action = 'Retrieving exam list for ' + student.fist_name + ' ' + student.last_name
            parent = student.parent.parent_mobile1
            log_entry(parent, action, "Normal", True)
        except Exception as e:
            print('unable to crete logbook entry')
            print ('Exception 500 from academics views.py %s %s' % (e.message, type(e)))

        return q.order_by('start_date')


class TestType(generics.ListCreateAPIView):
    serializer_class = TestTypeSerializer

    def get_queryset(self):
        test_id = self.kwargs['test_id']

        q = ClassTest.objects.filter(id=test_id)
        return q


class CompletedTestList(generics.ListCreateAPIView):
    serializer_class = TestSerializer

    def get_queryset(self):
        t = self.kwargs['teacher']

        the_teacher = Teacher.objects.get(email=t)
        q = ClassTest.objects.filter(teacher=the_teacher, is_completed=True).order_by('date_conducted')

        try:
            action = 'Retrieving completed test list for ' + the_teacher.first_name + ' ' + the_teacher.last_name
            log_entry(t, action, 'Normal', True)
        except Exception as e:
            print ('unable to create logbook entry. Exception 50 from academics views.py')
            print ('Exception 501 from academics views.py %s %s' % (e.message, type(e)))

        return q


class PendingTestList(generics.ListCreateAPIView):
    serializer_class = TestSerializer

    def get_queryset(self):
        t = self.kwargs['teacher']

        the_teacher = Teacher.objects.get(email=t)
        q = ClassTest.objects.filter(teacher=the_teacher, is_completed=False).order_by('date_conducted')

        try:
            action = 'Retrieving pending test list for ' + the_teacher.first_name + ' ' + the_teacher.last_name
            log_entry(t, action, 'Normal', True)
        except Exception as e:
            print ('unable to create logbook entry. Exception 50 from academics views.py')
            print ('Exception 502 from academics views.py %s %s' % (e.message, type(e)))

        return q


class PendingTestListParents(generics.ListAPIView):
    serializer_class = TestSerializer

    def get_queryset(self):
        s = self.kwargs['student']

        try:
            student = Student.objects.get(pk=s)
            the_class = student.current_class
            section = student.current_section
            q = ClassTest.objects.filter(the_class=the_class, section=section,
                                         date_conducted__gte=date.today()).order_by('date_conducted')

            try:
                parent_name = student.parent.parent_name
                action = 'Retrieving pending test list for ' + parent_name
                mobile = student.parent.parent_mobile1
                log_entry(mobile, action, 'Normal', True)
            except Exception as e:
                print ('unable to create logbook entry. Exception 50 from academics views.py')
                print ('Exception 503 from academics views.py %s %s' % (e.message, type(e)))

            return q
        except Exception as e:
            print ('Exception 370 from academics views.py %s %s' % (e.message, type(e)))
            print ('failed to retrieve pending test list for parents')


class ClassSectionForTest(generics.ListCreateAPIView):
    serializer_class = ClassSectionForTestSerializer

    def get_queryset(self):
        test_id = self.kwargs['id']

        q = ClassTest.objects.filter(pk=test_id)[:1]
        for p in q:
            print (p.the_class)
            print (p.section)
        return q


class MarksListForTest(generics.ListCreateAPIView):
    serializer_class = TestMarksSerializer

    def get_queryset(self):
        test_id = self.kwargs['test_id']
        t = ClassTest.objects.get(pk=test_id)

        q = TestResults.objects.filter(class_test=t).order_by('roll_no')
        return q


class TheCoScholastics(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = CoScholasticSerializer

    def get_queryset(self):
        t = self.kwargs['teacher']
        c = self.kwargs['class']
        s = self.kwargs['section']
        term = self.kwargs['term']
        teacher = Teacher.objects.get(email=t)
        school = teacher.school
        the_class = Class.objects.get(standard=c, school=school)
        section = Section.objects.get(section=s, school=school)

        # retrieve the grade list for this class/section/term, if it is already created
        q = CoScholastics.objects.filter(the_class=the_class, section=section, term=term)
        if q.exists():
            print('CoScholastics for ' + c + '-' + s + ' ' + term + ' already exists!')
            return q
        else:
            # the grade list for this class has not been created yet. Create for each student
            print('CoScholastics for ' + c + '-' + s + ' ' + term + ' not yet created. Hence creating...')
            students = Student.objects.filter(current_class=the_class, current_section=section)
            for s in students:
                coscholastic = CoScholastics(term=term, the_class=the_class, section=section, student=s)

                # if this is the second term, the student is most likely to be promoted to the next class
                if term == 'term2':
                    try:
                        next_class_sequence = the_class.sequence + 1
                        next_class_standard = Class.objects.get(school=school, sequence=next_class_sequence)
                        coscholastic.promoted_to_class = next_class_standard
                    except Exception as e:
                        print('failed to determine the class to be promoted for ' + s.fist_name + ' ' + s.last_name)
                        print ('Exception 710 from academics views.py %s %s' % (e.message, type(e)))
                try:
                    coscholastic.save()
                    print('created ' + term + ' CoScholastic entry for ' + s.fist_name + ' ' + s.last_name)
                except Exception as e:
                    print('failed to created ' + term + ' CoScholastic entry for ' +
                          s.fist_name + ' ' + s.last_name)
                    print ('Exception 700 from academics views.py %s %s' % (e.message, type(e)))
            # now the complete list has been created, it can be send to device
            q = CoScholastics.objects.filter(the_class=the_class, section=section, term=term)
            return q

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        print('starting to save Scholastic Grades')
        print('request=')
        print(request.body)
        data = json.loads(request.body)
        print ('json=')
        print (data)

        for key in data:
            result = CoScholastics.objects.get(pk=key)
            result.work_education = data[key]['work_education']
            result.art_education = data[key]['art_education']
            result.health_education = data[key]['health_education']
            result.discipline = data[key]['discipline']
            result.teacher_remarks = data[key]['teacher_remarks']
            result.promoted_to_class = data[key]['promoted_to_class']
            try:
                result.save()
                print('successfully saved CoScholastic Grades for ' +
                      result.student.fist_name + ' ' + result.student.last_name)
            except Exception as e:
                print('failed to save CoScholastic Grades')
                print ('Exception 750 from academics views.py %s %s' % (e.message, type(e)))
                context_dict['status'] = 'failed'
        context_dict['status'] = 'success'
        return JSONResponse(context_dict, status=200)


class HWList(generics.ListCreateAPIView):
    serializer_class = HWSerializer

    def get_queryset(self):
        user = self.kwargs['user']

        try:
            t = Teacher.objects.get(email=user)
            q = HW.objects.filter(teacher=t.email).order_by('due_date')

            try:
                action = 'Retrieving HW list for ' + t.first_name + ' ' + t.last_name
                log_entry(t.email, action, 'Normal', True)
            except Exception as e:
                print('unable to crete logbook entry')
                print ('Exception 504 from academics views.py %s %s' % (e.message, type(e)))
            return q
        except Exception as e:
            print('Exception 350 from academics view.py %s %s' % (e.message, type(e)))
            print('We need to retrieve the HW list for student')
            try:
                student = Student.objects.get(pk=user)
                school = student.school
                the_class = student.current_class
                section = student.current_section
                q = HW.objects.filter(school=school, the_class=the_class.standard, section=section.section)
                try:
                    action = 'Retrieving HW list for ' + student.fist_name + ' ' + student.last_name
                    parent_mobile = student.parent.parent_mobile1
                    log_entry(parent_mobile, action, 'Normal', True)
                except Exception as e:
                    print('unable to crete logbook entry')
                    print ('Exception 505 from academics views.py %s %s' % (e.message, type(e)))
                return q
            except Exception as e:
                print ('Exception 360 from academics views.py %s %s' % (e.message, type(e)))
                print('could not retrieve student with id %s' % user)


def get_hw_image(request, hw_id):
    context_dict =  {

    }
    context_dict['header'] = 'Send HW Image'
    if request.method == 'GET':
        try:
            hw = HW.objects.get(pk=hw_id)
            location = hw.location
            print('location = %s' % location)
            path = MEDIA_ROOT + '/' + str(location)
            print('filepath = %s' % path)
            wrapper = FileWrapper(open(path))
            content_type = mimetypes.guess_type(path)[0]
            print('content_type %s' % content_type)
            response = HttpResponse(wrapper, content_type=content_type)
            response['Content-Disposition'] = "attachment; filename=%s" % path
            try:
                action = 'Retrieving HW image created by ' + hw.teacher.first_name + ' ' + hw.teacher.last_name
                teacher = hw.teacher.email
                log_entry(teacher, action, 'Normal', True)
            except Exception as e:
                print('unable to crete logbook entry')
                print ('Exception 506 from academics views.py %s %s' % (e.message, type(e)))
            return response
        except Exception as e:
            print('Exception 330 from academics views.py %s %s' % (e.message, type(e)))
            response = HttpResponse(status=201)
            return response


@csrf_exempt
def create_hw(request):
    context_dict = {
    }
    context_dict['header'] = 'Create HW'
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            print('create hw process started')
            school_id = data['school_id']
            school = School.objects.get(id=school_id)
            teacher = data['teacher']
            t = Teacher.objects.get(email=teacher)
            print (t)
            print(teacher)
            the_class = data['class']
            print(the_class)
            c = Class.objects.get(school=school, standard=the_class)
            print (c)
            section = data['section']
            print(section)
            s = Section.objects.get(school=school, section=section)
            print (s)
            subject = data['subject']
            print(subject)
            sub = Subject.objects.get(school=school, subject_name=subject)
            print (sub)
            d = data['d']
            m = data['m']
            y = data['y']


            the_date = date(int(y), int(m), int(d))
            print (the_date)

            image_name = data['image_name']
            print(image_name)

            hw_image = data['hw_image']

            hw_image_file = ContentFile(base64.b64decode(hw_image), name=image_name)

            # save the home work
            hw = HW()
            hw.location = hw_image_file
            hw.school = school
            hw.teacher = teacher
            hw.the_class = the_class
            hw.section = section
            hw.subject = subject
            hw.due_date = the_date

            try:
                hw.save()
                context_dict['status'] = 'success'
                print(hw.location)
                try:
                    action = 'Creating HW for:  ' + the_class + '-' + section + ', Subject: ' + subject
                    log_entry(teacher, action, 'Normal', True)
                except Exception as e:
                    print('unable to crete logbook entry')
                    print ('Exception 508 from academics views.py %s %s' % (e.message, type(e)))
                return JSONResponse(context_dict, status=200)
            except Exception as e:
                print('Exception 310 from academics views.py = %s (%s)' % (e.message, type(e)))
                print('error while trying to save the homework uploaded by ' + teacher)
                context_dict['status'] = 'failed'
                return JSONResponse(context_dict, status=201)

        except Exception as e:
            print('failed to get the POST data for create hw')
            print('Exception 300 from academics views.py = %s (%s)' % (e.message, type(e)))
            context_dict['status'] = 'failed'
            return JSONResponse(context_dict, status=201)
    context_dict['status'] = 'success'
    return JSONResponse(context_dict, status=200)


@csrf_exempt
def create_test1(request, school_id, the_class, section, subject,
                teacher, d, m, y, max_marks, pass_marks, grade_based, comments, test_type):
    context_dict = {
    }
    context_dict['header'] = 'Create Test'
    if request.method == 'POST':
        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        school = School.objects.get(id=school_id)
        c = Class.objects.get(school=school, standard=the_class)
        print (c)
        s = Section.objects.get(school=school, section=section)
        print (s)
        sub = Subject.objects.get(school=school, subject_name=subject)
        print (sub)
        t = Teacher.objects.get(email=teacher)
        print (t)
        the_date = date(int(y), int(m), int(d))
        print (the_date)

        # check to see if this test has already been created.
        try:
            q = ClassTest.objects.filter(date_conducted=the_date, the_class=c, section=s, subject=sub, teacher=t)
            print (q.count())

            # make an entry to database only it is a fresh entry
            if q.count() == 0:
                test = ClassTest(date_conducted=the_date)
                test.the_class = c
                test.section = s
                test.subject = sub
                test.teacher = t
                test.max_marks = float(max_marks)  # max_marks and pass_marks are passed as strings
                test.passing_marks = float(pass_marks)
                test.test_type = test_type

                if grade_based == '0':
                    print ('grade_based is 0')
                    test.grade_based = True

                if grade_based == '1':
                    print ('grade_based is 1')
                    test.grade_based = False

                print (grade_based)

                test.syllabus = comments
                test.test_type = test_type
                test.is_completed = False

                try:
                    test.save()
                    try:
                        action = 'Created test for '  + the_class + '-' + section + ', Subject: ' + subject
                        log_entry(t.email, action, 'Normal', True)
                    except Exception as e:
                        print('unable to crete logbook entry')
                        print ('Exception 510 from academics views.py %s %s' % (e.message, type(e)))
                    print ('test successfully created')

                except Exception as e:
                    print ('Test creation failed')
                    print ('Exception 509 from academics views.py Exception = %s (%s)' % (e.message, type(e)))
                    return HttpResponse('Test Creation Failed')

                # now, create entry for each student in table TestResults. We need to retrieve the list of student
                # of the class associated with this test
                student_list = Student.objects.filter(school=school, current_section__section=section,
                                                      current_class__standard=the_class, active_status=True)
                for student in student_list:
                    # -5000.00 marks indicate null value
                    test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                              student=student, marks_obtained=-5000.00, grade='')
                    try:
                        test_result.save()
                        print (' test results successfully created for % s %s' % (student.fist_name, student.last_name))

                        # 21/09/2017 some more data need to be created for a Term test
                        try:
                            if test_type == 'term':
                                term_test_result = TermTestResult(test_result=test_result, periodic_test_marks=-5000.0,
                                                                  note_book_marks=-5000.0, sub_enrich_marks=-5000.0)
                                term_test_result.save()
                                print (' term test results successfully created for % s %s' %
                                       (student.fist_name, student.last_name))
                        except Exception as e:
                            print ('failed to create term test results')
                            print ('Exception 600-A from acacemics views.py = %s (%s)' % (e.message, type(e)))
                            return HttpResponse('Failed to create term test results')
                    except Exception as e:
                        print ('failed to create test results')
                        print ('Exception 600 from acacemics views.py = %s (%s)' % (e.message, type(e)))
                        return HttpResponse('Failed to create test results')
            else:
                print ('Test already exist')
                return HttpResponse('Test already exist')
        except Exception as e:
            print ('Exception 601 fro academics views.py = %s (%s)' % (e.message, type(e)))
            return HttpResponse('Failed')

    # this view is being called from mobile. We use dummy template so that we dont' run into exception
    # return render(request, 'classup/dummy.html')
    return HttpResponse('OK')



# we need to exempt this view from csrf verification. Will be updated in next version when
# we will implement authentication
@csrf_exempt
def create_test(request, school_id, the_class, section, subject,
                teacher, d, m, y, max_marks, pass_marks, grade_based, comments):
    if request.method == 'POST':
        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        school = School.objects.get(id=school_id)
        c = Class.objects.get(school=school, standard=the_class)
        print (c)
        s = Section.objects.get(school=school, section=section)
        print (s)
        sub = Subject.objects.get(school=school, subject_name=subject)
        print (sub)
        t = Teacher.objects.get(email=teacher)
        print (t)
        the_date = date(int(y), int(m), int(d))
        print (the_date)

        # check to see if this test has already been created.
        try:
            q = ClassTest.objects.filter(date_conducted=the_date, the_class=c, section=s, subject=sub, teacher=t)
            print (q.count())

            # make an entry to database only it is a fresh entry
            if q.count() == 0:
                test = ClassTest(date_conducted=the_date)
                test.the_class = c
                test.section = s
                test.subject = sub
                test.teacher = t
                test.max_marks = float(max_marks)  # max_marks and pass_marks are passed as strings
                test.passing_marks = float(pass_marks)

                if grade_based == '0':
                    print ('grade_based is 0')
                    test.grade_based = True

                if grade_based == '1':
                    print ('grade_based is 1')
                    test.grade_based = False

                print (grade_based)

                test.test_type = comments
                test.is_completed = False

                try:
                    test.save()
                    try:
                        action = 'Created test for '  + the_class + '-' + section + ', Subject: ' + subject
                        log_entry(t.email, action, 'Normal', True)
                    except Exception as e:
                        print('unable to create logbook entry')
                        print ('Exception 510 from academics views.py %s %s' % (e.message, type(e)))
                    print ('test successfully created')

                except Exception as e:
                    print ('Test creation failed')
                    print ('Exception 509 from academics views.py Exception = %s (%s)' % (e.message, type(e)))
                    return HttpResponse('Test Creation Failed')

                # now, create entry for each student in table TestResults. We need to retrieve the list of student
                # of the class associated with this test
                student_list = Student.objects.filter(school=school, current_section__section=section,
                                                      current_class__standard=the_class, active_status=True)
                for student in student_list:
                    # -5000.00 marks indicate null value
                    test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                              student=student, marks_obtained=-5000.00, grade='')
                    try:
                        test_result.save()
                        print (' test results successfully created')
                    except Exception as e:
                        print ('failed to create test results')
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        return HttpResponse('Failed to create test results')
            else:
                print ('Test already exist')
                return HttpResponse('Test already exist')
        except Exception as e:
            print ('Exception = %s (%s)' % (e.message, type(e)))
            return HttpResponse('Failed')

    # this view is being called from mobile. We use dummy template so that we dont' run into exception
    # return render(request, 'classup/dummy.html')
    return HttpResponse('OK')


def get_grade(marks):
    if marks <= 100 and marks > 90:
        grade = 'A1'
        return grade
    if marks <= 90 and marks > 80:
        grade = 'A2'
        return grade
    if marks <= 80 and marks > 70:
        grade = 'B1'
        return grade
    if marks <= 70 and marks > 60:
        grade = 'B2'
        return grade
    if marks <= 60 and marks > 50:
        grade = 'C1'
        return grade
    if marks <= 50 and marks > 40:
        grade = 'C2'
        return grade
    if marks <= 40 and marks > 32:
        grade = 'D'
        return grade
    if marks <= 32:
        grade = 'E (Needs Improvement)'
        return grade


# we need to exempt this view from csrf verification. Will be updated in next version when
# we will implement authentication


@csrf_exempt
def prepare_results(request, school_id, the_class, section):
    school = School.objects.get(id=school_id)
    school_name = school.school_name
    print(school)
    standard = Class.objects.get(school=school, standard=the_class)
    print(standard)
    sec = Section.objects.get(school=school, section=section)
    print(sec)

    if request.method == 'GET':
        print(request.body)
        whole_class = request.GET.get('whole_class')
        print(whole_class)
        selected_student = request.GET.get('selected_student')
        print (selected_student)

        # 20/10/2017 - now the grand loop starts!

        def get_marks_and_print_report_card(student, title):
            return

        if whole_class == 'true':
            pdf_name = the_class + '-' + section + '_Term1_Results.pdf'
            print(pdf_name)

            response = HttpResponse(content_type='application/pdf')
            content_disposition = 'attachment; filename=' + pdf_name
            print (content_disposition)
            response['Content-Disposition'] = content_disposition
            print(response)
            c = canvas.Canvas(response, pagesize=A4, bottomup=1)

            #c.drawString(130, top, school_name)
            # get the list of all the students, then get the marks of each test conducted for this exam
            students = Student.objects.filter(school=school, current_class=standard, current_section=sec)
            for s in students:
                print('Entering loop')

                c.translate(inch, inch)
                font = 'Times-Bold'
                c.setFont(font, 14)
                font = 'Times-Bold'
                top = 700
                c.setFont(font, 14)
                c.drawString(135, top, school_name)

                print('marks dictionary initialized')

                line_top = top - 10

                c.line(0, line_top, 6 * inch, line_top)

                session_top = line_top - 15
                session = 'Academic Session 2017-18'
                c.setFont(font, 10)
                c.drawString(152, session_top, session)
                print('heading created')

                report_card_top = session_top - 10
                report_card = 'Report Card for Class ' + the_class + '-' + section
                c.drawString(152, report_card_top, report_card)

                tab = 80
                stu_detail_top = report_card_top - 20
                c.setFont(font, 10)

                adm_no_lbl = 'Admission No:'
                c.drawString(0, stu_detail_top, adm_no_lbl)
                c.drawString(tab, stu_detail_top, s.student_erp_id)

                stu_name_lbl = 'Student Name:'
                c.drawString(0, stu_detail_top - 15, stu_name_lbl)
                c.drawString(tab, stu_detail_top - 15, s.fist_name + ' ' + s.last_name)

                father_name_lbl = 'Father Name:'
                c.drawString(0, stu_detail_top - 30, father_name_lbl)
                c.drawString(tab, stu_detail_top - 30, s.parent.parent_name)

                dob_lbl = 'Date of Birth:'
                c.drawString(0, stu_detail_top - 45, dob_lbl)
                try:
                    d = DOB.objects.get(student=s)
                    dob = d.dob
                    c.drawString(tab, stu_detail_top - 45, dob)
                except Exception as e:
                    print ('date of birth not yet set for %s %s ' % (s.fist_name, s.last_name))
                    print('Exception 23102017-A from academics views.py %s %s ' % (e.message, type(e)))

                class_sec_lbl = 'Class/Section:'
                c.drawString(0, stu_detail_top - 60, class_sec_lbl)
                c.drawString(tab, stu_detail_top - 60, the_class + '-' + section)
                print('report heading prepared')

                exam = Exam.objects.get(school=school, title='Term1')
                print(exam)
                start_date = exam.start_date
                end_date = exam.end_date

                try:
                    lang1 = 'English'
                    lang1_sub = Subject.objects.get(school=school, subject_name=lang1)
                    lang1_test = ClassTest.objects.get(subject=lang1_sub, the_class=standard, section=sec,
                                                       date_conducted__gte=start_date, date_conducted__lte=end_date)
                    tr = TestResults.objects.get(class_test=lang1_test, student=s)

                    lang1_main = tr.marks_obtained
                    term_tr = TermTestResult.objects.get(test_result=tr)

                    lang1_pa = term_tr.periodic_test_marks

                    lang1_notebook = term_tr.note_book_marks

                    lang1_sub_enrich = term_tr.sub_enrich_marks

                    lang1_total = float(lang1_main) + float(lang1_pa) + float(lang1_notebook) + float(lang1_sub_enrich)

                    lang1_grade = get_grade(lang1_total)
                    print(lang1_grade)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-A from academics views.py %s %s' % (e.message, type(e)))

                try:
                    lang2 = 'Hindi'
                    lang2_sub = Subject.objects.get(school=school, subject_name=lang2)
                    lang2_test = ClassTest.objects.get(subject=lang2_sub, the_class=standard, section=sec,
                                                       date_conducted__gte=start_date, date_conducted__lte=end_date)
                    tr = TestResults.objects.get(class_test=lang2_test, student=s)
                    lang2_main = tr.marks_obtained
                    term_tr = TermTestResult.objects.get(test_result=tr)

                    lang2_pa = term_tr.periodic_test_marks

                    lang2_notebook = term_tr.note_book_marks

                    lang2_sub_enrich = term_tr.sub_enrich_marks

                    lang2_total = float(lang2_main) + float(lang2_pa) + float(lang2_notebook) + float(lang2_sub_enrich)

                    lang2_grade = get_grade(lang2_total)
                    print(lang2_grade)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-B from academics views.py %s %s' % (e.message, type(e)))

                try:
                    lang3 = 'Sanskrit'
                    lang3_sub = Subject.objects.get(school=school, subject_name=lang3)
                    lang3_test = ClassTest.objects.get(subject=lang3_sub, the_class=standard, section=sec,
                                                       date_conducted__gte=start_date, date_conducted__lte=end_date)
                    tr = TestResults.objects.get(class_test=lang3_test, student=s)
                    lang3_main = tr.marks_obtained
                    term_tr = TermTestResult.objects.get(test_result=tr)

                    lang3_pa = term_tr.periodic_test_marks

                    lang3_notebook = term_tr.note_book_marks

                    lang3_sub_enrich = term_tr.sub_enrich_marks

                    lang3_total = float(lang3_main) + float(lang3_pa) + float(lang3_notebook) + float(lang3_sub_enrich)

                    lang3_grade = get_grade(lang3_total)
                    print(lang3_grade)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-C from academics views.py %s %s' % (e.message, type(e)))

                try:
                    maths = 'Mathematics'
                    maths_sub = Subject.objects.get(school=school, subject_name=maths)
                    maths_test = ClassTest.objects.get(subject=maths_sub, the_class=standard, section=sec,
                                                       date_conducted__gte=start_date, date_conducted__lte=end_date)
                    tr = TestResults.objects.get(class_test=maths_test, student=s)
                    maths_main = tr.marks_obtained
                    term_tr = TermTestResult.objects.get(test_result=tr)

                    maths_pa = term_tr.periodic_test_marks

                    maths_notebook = term_tr.note_book_marks

                    maths_sub_enrich = term_tr.sub_enrich_marks

                    maths_total = float(maths_main) + float(maths_pa) + float(maths_notebook) + float(maths_sub_enrich)


                    maths_grade = get_grade(maths_total)
                    print(maths_grade)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-D from academics views.py %s %s' % (e.message, type(e)))

                try:
                    science = 'Science'
                    science_sub = Subject.objects.get(school=school, subject_name=science)
                    science_test = ClassTest.objects.get(subject=science_sub, the_class=standard, section=sec,
                                                       date_conducted__gte=start_date, date_conducted__lte=end_date)
                    tr = TestResults.objects.get(class_test=science_test, student=s)
                    science_main = tr.marks_obtained
                    term_tr = TermTestResult.objects.get(test_result=tr)

                    science_pa = term_tr.periodic_test_marks

                    science_notebook = term_tr.note_book_marks

                    science_sub_enrich = term_tr.sub_enrich_marks

                    science_total = float(science_main) + float(science_pa) + \
                                    float(science_notebook) + float(science_sub_enrich)

                    science_grade = get_grade(science_total)
                    print(science_grade)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-E from academics views.py %s %s' % (e.message, type(e)))

                try:
                    sst = 'Social Studies'
                    sst_sub = Subject.objects.get(school=school, subject_name=sst)
                    sst_test = ClassTest.objects.get(subject=sst_sub, the_class=standard, section=sec,
                                                         date_conducted__gte=start_date, date_conducted__lte=end_date)
                    tr = TestResults.objects.get(class_test=sst_test, student=s)
                    sst_main = tr.marks_obtained
                    term_tr = TermTestResult.objects.get(test_result=tr)

                    sst_pa = term_tr.periodic_test_marks

                    sst_notebook = term_tr.note_book_marks

                    sst_sub_enrich = term_tr.sub_enrich_marks

                    sst_total = float(sst_main) + float(sst_pa) + float(sst_notebook) + float(sst_sub_enrich)

                    sst_grade = get_grade(sst_total)
                    print(sst_grade)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-F from academics views.py %s %s' % (e.message, type(e)))

                try:
                    comp = 'Computer'
                    comp_sub = Subject.objects.get(school=school, subject_name=comp)
                    comp_test = ClassTest.objects.get(subject=comp_sub, the_class=standard, section=sec,
                                                     date_conducted__gte=start_date, date_conducted__lte=end_date)
                    tr = TestResults.objects.get(class_test=comp_test, student=s)
                    comp_main = tr.marks_obtained
                    term_tr = TermTestResult.objects.get(test_result=tr)

                    comp_pa = term_tr.periodic_test_marks

                    comp_notebook = term_tr.note_book_marks

                    comp_sub_enrich = term_tr.sub_enrich_marks

                    comp_total = float(comp_main) + float(comp_pa) + float(comp_notebook) + float(comp_sub_enrich)

                    comp_grade = get_grade(comp_total)
                    print(comp_grade)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-G from academics views.py %s %s' % (e.message, type(e)))

                try:
                    data1 = [['Scholastic\nAreas', 'Term-1 (100 Marks)', '', '', '', '', ''],
                             ['Sub Name', 'Half\nYearly\nExam\n(80)', 'Per Test\n(10)', 'Note Book\n(5)', 'Sub\nEnrichment\n(5)',

                              'Marks\nObtained\n(100)', 'Grade'],
                             [lang1, lang1_main, lang1_pa, lang1_notebook, lang1_sub_enrich, lang1_total, lang1_grade],
                             [lang2, lang2_main, lang2_pa, lang2_notebook, lang2_sub_enrich, lang2_total, lang2_grade],
                             [lang3, lang3_main, lang3_pa, lang3_notebook, lang3_sub_enrich, lang3_total, lang3_grade],
                             [maths, maths_main, maths_pa, maths_notebook, maths_sub_enrich, maths_total, maths_grade],
                             [science, science_main, science_pa, science_notebook,
                              science_sub_enrich, science_total, science_grade],
                             [sst, sst_main, sst_pa, sst_notebook, sst_sub_enrich, sst_total, sst_grade],
                             [comp, comp_total, comp_pa, comp_notebook, comp_sub_enrich, comp_total, comp_grade]]

                    table1 = Table(data1)
                    table1.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                                ('ALIGN', (1, 0), (6, 0), 'CENTER'),
                                                ('SPAN', (1, 0), (6, 0)),
                                                ('FONTSIZE', (0, 0), (-1, -1), 8),
                                                ('FONT', (0, 0), (6, 0), 'Times-Bold'),
                                                ('FONT', (0, 1), (0, 1), 'Times-Bold')
                                                ]))

                    table1_top = stu_detail_top - 275
                    table1.wrapOn(c, 0, 0)
                    table1.drawOn(c, 0, table1_top)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-H from academics views.py %s %s' % (e.message, type(e)))

                # get the CoScholastic Grades for this student
                co_scl = CoScholastics.objects.get(term='Term1', student=s)
                work_ed = co_scl.work_education
                art_ed = co_scl.art_education
                health_ed = co_scl.health_education
                dscpln = co_scl.discipline
                remark = co_scl.teacher_remarks

                data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale', ''],
                         ['Work Education (or Pre-vocational Education', work_ed],
                         ['Art Education', art_ed],
                         ['Health & Physical Education', health_ed]]
                table2_top = table1_top - 100
                table2 = Table(data2)
                table2.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                            ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                                            ('SPAN', (0, 0), (1, 0)),
                                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                                            ('FONT', (0, 0), (1, 0), 'Times-Bold')
                                            ]))
                table2.wrapOn(c, 0, 0)
                table2.drawOn(c, 0, table2_top)

                data3 = [['Grade', 'Grade'],
                         ['Discipline: Term-1[On a 3-point(A-C) grading scale', dscpln]]
                table3_top = table2_top - 50
                table3 = Table(data3)
                table3.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                            ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('ALIGN', (0, 0), (1, 0), 'RIGHT'),
                                            ('SPAN', (0, 0), (1, 0)),
                                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                                            ('FONT', (0, 0), (0, 0), 'Times-Bold')
                                            ]))
                table3.wrapOn(c, 0, 0)
                table3.drawOn(c, 0, table3_top)

                c.drawString(0, table3_top - 20, 'Class Teacher Remarks: ')
                c.drawString(tab+30, table3_top - 20, remark)
                c.drawString(0, table3_top - 45, 'Place & Date:')
                c.drawString(150, table3_top - 45, 'Signature of Class Teacher')
                c.drawString(300, table3_top - 45, 'Signature of Principal')

                c.line(0, table3_top - 50, 6 * inch, table3_top - 50)
                c.drawString(170, table3_top - 60, "Instructions")
                c.drawString(0, table3_top - 70, "Grading Scale for Scholastic Areas: "
                                                 "Grades are awarded on a 8-point grading scales as follows - ")

                data4 = [['MARKS RANGE', 'GRADE'],
                         ['91 - 100', 'A 1'],
                         ['81 - 90', 'A 2'],
                         ['71 - 80', 'B 1'],
                         ['61 - 70', 'B 2'],
                         ['51 - 60', 'C 1'],
                         ['41 - 50', 'C 2'],
                         ['33 - 40', 'D'],
                         ['32 & Below', 'E (Needs improvement)']]
                table4 = Table(data4)
                table4.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                            ('FONT', (0, 0), (1, 0), 'Times-Bold'),
                                            ('FONTSIZE', (0, 0), (-1, -1), 8)]))
                table4.wrapOn(c, 0, 0)
                table4.drawOn(c, 120, table3_top - 250)

                c.showPage()
            try:
                c.save()
            except Exception as e:
                print('error in saving the pdf')
                print ('Exception 21102017-P from academics views.py %s %s' % (e.message, type(e)))
            print('about to send the response')
            return response
        else:
            adm_no = selected_student.partition('(')[-1].rpartition(')')[0]
            s = Student.objects.get(school=school, student_erp_id=adm_no)
            print(s)

            pdf_name = s.fist_name + '_' + s.last_name + '_Term1_Results.pdf'
            print(pdf_name)

            response = HttpResponse(content_type='application/pdf')
            content_disposition = 'attachment; filename=' + pdf_name
            print (content_disposition)
            response['Content-Disposition'] = content_disposition
            print(response)

            c = canvas.Canvas(response, pagesize=A4, bottomup=1)
            c.translate(inch, inch)
            font = 'Times-Bold'
            c.setFont(font, 14)
            top = 700
            c.setFont(font, 14)
            c.drawString(130, top, school_name)

            line_top = top - 10

            c.line(0, line_top, 6 * inch, line_top)

            session_top = line_top - 15
            session = 'Academic Session 2017-18'
            c.setFont(font, 10)
            c.drawString(152, session_top, session)
            print('heading created')

            report_card_top = session_top - 10
            report_card = 'Report Card for Class ' + the_class + '-' + section
            c.drawString(152, report_card_top, report_card)

            tab = 80
            stu_detail_top = report_card_top - 20
            c.setFont(font, 10)

            adm_no_lbl = 'Admission No:'
            c.drawString(0, stu_detail_top, adm_no_lbl)
            c.drawString(tab, stu_detail_top, s.student_erp_id)

            stu_name_lbl = 'Student Name:'
            c.drawString(0, stu_detail_top - 15, stu_name_lbl)
            c.drawString(tab, stu_detail_top - 15, s.fist_name + ' ' + s.last_name)

            father_name_lbl = 'Father Name:'
            c.drawString(0, stu_detail_top - 30, father_name_lbl)
            c.drawString(tab, stu_detail_top - 30, s.parent.parent_name)

            dob_lbl = 'Date of Birth:'
            c.drawString(0, stu_detail_top - 45, dob_lbl)

            class_sec_lbl = 'Class/Section:'
            c.drawString(0, stu_detail_top - 60, class_sec_lbl)
            c.drawString(tab, stu_detail_top - 60, the_class + '-' + section)
            print('report heading prepared')

            exam = Exam.objects.get(school=school, title='Term1')
            print(exam)
            start_date = exam.start_date
            end_date = exam.end_date

            try:
                lang1 = 'English'
                lang1_sub = Subject.objects.get(school=school, subject_name=lang1)
                lang1_test = ClassTest.objects.get(subject=lang1_sub, the_class=standard, section=sec,
                                                   date_conducted__gte=start_date, date_conducted__lte=end_date)
                tr = TestResults.objects.get(class_test=lang1_test, student=s)

                lang1_main = tr.marks_obtained
                term_tr = TermTestResult.objects.get(test_result=tr)

                lang1_pa = term_tr.periodic_test_marks

                lang1_notebook = term_tr.note_book_marks

                lang1_sub_enrich = term_tr.sub_enrich_marks

                lang1_total = float(lang1_main) + float(lang1_pa) + float(lang1_notebook) + float(lang1_sub_enrich)

                lang1_grade = get_grade(lang1_total)
                print(lang1_grade)
            except Exception as e:
                print('Error while preparing results')
                print ('Exception 21102017-A from academics views.py %s %s' % (e.message, type(e)))

            try:
                lang2 = 'Hindi'
                lang2_sub = Subject.objects.get(school=school, subject_name=lang2)
                lang2_test = ClassTest.objects.get(subject=lang2_sub, the_class=standard, section=sec,
                                                   date_conducted__gte=start_date, date_conducted__lte=end_date)
                tr = TestResults.objects.get(class_test=lang2_test, student=s)
                lang2_main = tr.marks_obtained
                term_tr = TermTestResult.objects.get(test_result=tr)

                lang2_pa = term_tr.periodic_test_marks

                lang2_notebook = term_tr.note_book_marks

                lang2_sub_enrich = term_tr.sub_enrich_marks

                lang2_total = float(lang2_main) + float(lang2_pa) + float(lang2_notebook) + float(lang2_sub_enrich)

                lang2_grade = get_grade(lang2_total)
                print(lang2_grade)
            except Exception as e:
                print('Error while preparing results')
                print ('Exception 21102017-B from academics views.py %s %s' % (e.message, type(e)))

            try:
                lang3 = 'Sanskrit'
                lang3_sub = Subject.objects.get(school=school, subject_name=lang3)
                lang3_test = ClassTest.objects.get(subject=lang3_sub, the_class=standard, section=sec,
                                                   date_conducted__gte=start_date, date_conducted__lte=end_date)
                tr = TestResults.objects.get(class_test=lang3_test, student=s)
                lang3_main = tr.marks_obtained
                term_tr = TermTestResult.objects.get(test_result=tr)

                lang3_pa = term_tr.periodic_test_marks

                lang3_notebook = term_tr.note_book_marks

                lang3_sub_enrich = term_tr.sub_enrich_marks

                lang3_total = float(lang3_main) + float(lang3_pa) + float(lang3_notebook) + float(lang3_sub_enrich)

                lang3_grade = get_grade(lang3_total)
                print(lang3_grade)
            except Exception as e:
                print('Error while preparing results')
                print ('Exception 21102017-C from academics views.py %s %s' % (e.message, type(e)))

            try:
                maths = 'Mathematics'
                maths_sub = Subject.objects.get(school=school, subject_name=maths)
                maths_test = ClassTest.objects.get(subject=maths_sub, the_class=standard, section=sec,
                                                   date_conducted__gte=start_date, date_conducted__lte=end_date)
                tr = TestResults.objects.get(class_test=maths_test, student=s)
                maths_main = tr.marks_obtained
                term_tr = TermTestResult.objects.get(test_result=tr)

                maths_pa = term_tr.periodic_test_marks

                maths_notebook = term_tr.note_book_marks

                maths_sub_enrich = term_tr.sub_enrich_marks

                maths_total = float(maths_main) + float(maths_pa) + float(maths_notebook) + float(maths_sub_enrich)


                maths_grade = get_grade(maths_total)
                print(maths_grade)
            except Exception as e:
                print('Error while preparing results')
                print ('Exception 21102017-D from academics views.py %s %s' % (e.message, type(e)))

            try:
                science = 'Science'
                science_sub = Subject.objects.get(school=school, subject_name=science)
                science_test = ClassTest.objects.get(subject=science_sub, the_class=standard, section=sec,
                                                     date_conducted__gte=start_date, date_conducted__lte=end_date)
                tr = TestResults.objects.get(class_test=science_test, student=s)
                science_main = tr.marks_obtained
                term_tr = TermTestResult.objects.get(test_result=tr)

                science_pa = term_tr.periodic_test_marks

                science_notebook = term_tr.note_book_marks

                science_sub_enrich = term_tr.sub_enrich_marks

                science_total = float(science_main) + float(science_pa) + \
                                float(science_notebook) + float(science_sub_enrich)

                science_grade = get_grade(science_total)
                print(science_grade)
            except Exception as e:
                print('Error while preparing results')
                print ('Exception 21102017-E from academics views.py %s %s' % (e.message, type(e)))

            try:
                sst = 'Social Studies'
                sst_sub = Subject.objects.get(school=school, subject_name=sst)
                sst_test = ClassTest.objects.get(subject=sst_sub, the_class=standard, section=sec,
                                                 date_conducted__gte=start_date, date_conducted__lte=end_date)
                tr = TestResults.objects.get(class_test=sst_test, student=s)
                sst_main = tr.marks_obtained
                term_tr = TermTestResult.objects.get(test_result=tr)

                sst_pa = term_tr.periodic_test_marks

                sst_notebook = term_tr.note_book_marks

                sst_sub_enrich = term_tr.sub_enrich_marks

                sst_total = float(sst_main) + float(sst_pa) + float(sst_notebook) + float(sst_sub_enrich)

                sst_grade = get_grade(sst_total)
                print(sst_grade)
            except Exception as e:
                print('Error while preparing results')
                print ('Exception 21102017-F from academics views.py %s %s' % (e.message, type(e)))

            try:
                comp = 'Computer'
                comp_sub = Subject.objects.get(school=school, subject_name=comp)
                comp_test = ClassTest.objects.get(subject=comp_sub, the_class=standard, section=sec,
                                                  date_conducted__gte=start_date, date_conducted__lte=end_date)
                tr = TestResults.objects.get(class_test=comp_test, student=s)
                comp_main = tr.marks_obtained
                term_tr = TermTestResult.objects.get(test_result=tr)

                comp_pa = term_tr.periodic_test_marks

                comp_notebook = term_tr.note_book_marks

                comp_sub_enrich = term_tr.sub_enrich_marks

                comp_total = float(comp_main) + float(comp_pa) + float(comp_notebook) + float(comp_sub_enrich)

                comp_grade = get_grade(comp_total)
                print(comp_grade)
            except Exception as e:
                print('Error while preparing results')
                print ('Exception 21102017-G from academics views.py %s %s' % (e.message, type(e)))

            try:
                data1 = [['Scholastic\nAreas', 'Term-1 (100 Marks)', '', '', '', '', ''],
                         ['Sub Name', 'Half\nYearly\nExam\n(80)', 'Per Test\n(10)', 'Note Book\n(5)',
                          'Sub\nEnrichment\n(5)',

                          'Marks\nObtained\n(100)', 'Grade'],
                         [lang1, lang1_main, lang1_pa, lang1_notebook, lang1_sub_enrich, lang1_total, lang1_grade],
                         [lang2, lang2_main, lang2_pa, lang2_notebook, lang2_sub_enrich, lang2_total, lang2_grade],
                         [lang3, lang3_main, lang3_pa, lang3_notebook, lang3_sub_enrich, lang3_total, lang3_grade],
                         [maths, maths_main, maths_pa, maths_notebook, maths_sub_enrich, maths_total, maths_grade],
                         [science, science_main, science_pa, science_notebook,
                          science_sub_enrich, science_total, science_grade],
                         [sst, sst_main, sst_pa, sst_notebook, sst_sub_enrich, sst_total, sst_grade],
                         [comp, comp_total, comp_pa, comp_notebook, comp_sub_enrich, comp_total, comp_grade]]

                table1 = Table(data1)
                table1.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                            ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('ALIGN', (1, 0), (6, 0), 'CENTER'),
                                            ('SPAN', (1, 0), (6, 0)),
                                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                                            ('FONT', (0, 0), (6, 0), 'Times-Bold'),
                                            ('FONT', (0, 1), (0, 1), 'Times-Bold')
                                            ]))

                table1_top = stu_detail_top - 275
                table1.wrapOn(c, 0, 0)
                table1.drawOn(c, 0, table1_top)
            except Exception as e:
                print('Error while preparing results')
                print ('Exception 21102017-H from academics views.py %s %s' % (e.message, type(e)))

            # get the CoScholastic Grades for this student
            co_scl = CoScholastics.objects.get(term='Term1', student=s)
            work_ed = co_scl.work_education
            art_ed = co_scl.art_education
            health_ed = co_scl.health_education
            dscpln = co_scl.discipline
            remark = co_scl.teacher_remarks

            data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale', ''],
                     ['Work Education (or Pre-vocational Education', work_ed],
                     ['Art Education', art_ed],
                     ['Health & Physical Education', health_ed]]
            table2_top = table1_top - 100
            table2 = Table(data2)
            table2.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                        ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                                        ('SPAN', (0, 0), (1, 0)),
                                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                                        ('FONT', (0, 0), (1, 0), 'Times-Bold')
                                        ]))
            table2.wrapOn(c, 0, 0)
            table2.drawOn(c, 0, table2_top)

            data3 = [['Grade', 'Grade'],
                     ['Discipline: Term-1[On a 3-point(A-C) grading scale', dscpln]]
            table3_top = table2_top - 50
            table3 = Table(data3)
            table3.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                        ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                        ('ALIGN', (0, 0), (1, 0), 'RIGHT'),
                                        ('SPAN', (0, 0), (1, 0)),
                                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                                        ('FONT', (0, 0), (0, 0), 'Times-Bold')
                                        ]))
            table3.wrapOn(c, 0, 0)
            table3.drawOn(c, 0, table3_top)

            c.drawString(0, table3_top - 20, 'Class Teacher Remarks: ')
            c.drawString(tab + 30, table3_top - 20, remark)
            c.drawString(0, table3_top - 45, 'Place & Date:')
            c.drawString(150, table3_top - 45, 'Signature of Class Teacher')
            c.drawString(300, table3_top - 45, 'Signature of Principal')

            c.line(0, table3_top - 50, 6 * inch, table3_top - 50)
            c.drawString(170, table3_top - 60, "Instructions")
            c.drawString(0, table3_top - 70, "Grading Scale for Scholastic Areas: "
                                             "Grades are awarded on a 8-point grading scales as follows - ")

            data4 = [['MARKS RANGE', 'GRADE'],
                     ['91 - 100', 'A 1'],
                     ['81 - 90', 'A 2'],
                     ['71 - 80', 'B 1'],
                     ['61 - 70', 'B 2'],
                     ['51 - 60', 'C 1'],
                     ['41 - 50', 'C 2'],
                     ['33 - 40', 'D'],
                     ['32 & Below', 'E (Needs improvement)']]
            table4 = Table(data4)
            table4.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                        ('FONT', (0, 0), (1, 0), 'Times-Bold'),
                                        ('FONTSIZE', (0, 0), (-1, -1), 8)]))
            table4.wrapOn(c, 0, 0)
            table4.drawOn(c, 120, table3_top - 250)

            c.showPage()
            c.save()
            return response
    return HttpResponse()


@csrf_exempt
def save_marks(request):
    if request.method == 'POST':
        response = {

        }
        print ('request.body=')
        print (request.body)
        # convert the raw data received to json
        data = json.loads(request.body)
        print ('json=')
        print (data)

        # determine whether this test is marks based or grade based
        grade_based = False
        for key in data:
            test = ClassTest.objects.get(testresults__id=key)
            break  # because we can get the test object with the first key only

        if test.grade_based:
            grade_based = True
            print ('this is a grade based test')

        # iterate over json and save/update marks
        for key in data:
            tr = TestResults.objects.get(pk=key)

            if grade_based:
                print ('saving grade....')
                tr.grade = data[key]
            else:
                tr.marks_obtained = float(data[key]['marks'])
                if test.test_type == 'term':
                    print('term test')
                    ttr = TermTestResult.objects.get(test_result=tr)
                    print(ttr)
                    ttr.periodic_test_marks = float(data[key]['pa'])
                    ttr.note_book_marks = float(data[key]['notebook'])
                    ttr.sub_enrich_marks = float(data[key]['subject_enrich'])
                    try:
                        ttr.save()
                        try:
                            action = 'Saved Term Test Results for ' + tr.student.fist_name + ' ' + tr.student.last_name
                            action += ' ' + test.the_class.standard + '-' + test.section.section
                            action += ' ' + test.subject.subject_name
                            teacher = test.teacher.email
                            log_entry(teacher, action, 'Normal', True)
                        except Exception as e:
                            print('unable to create logbook entry')
                            print ('Exception 511-A from academics views.py %s %s' % (e.message, type(e)))
                    except Exception as e:
                        print('unable to save Term Test Marks')
                        print ('Exception 512-A from academics views.py %s %s' % (e.message, type(e)))
            try:
                tr.save()
                try:
                    action = 'Saved Test Results for ' + tr.student.fist_name + ' ' + tr.student.last_name
                    action += ' ' + test.the_class.standard + '-' + test.section.section
                    action += ' ' + test.subject.subject_name
                    teacher = test.teacher.email
                    log_entry(teacher, action, 'Normal', True)
                except Exception as e:
                    print('unable to create logbook entry')
                    print ('Exception 511 from academics views.py %s %s' % (e.message, type(e)))
            except Exception as e:
                print('unable to save marks')
                print ('Exception 512 from academics viws.py = %s (%s)' % (e.message, type(e)))
        response["status"] = "success"

        return JSONResponse(response, status=200)


@csrf_exempt
def submit_marks(request, school_id):
    t1 = datetime.datetime.now()
    message_list = {

    }
    if request.method == 'POST':
        response = {

        }
        print ('request.body=')
        print (request.body)
        school = School.objects.get(id=school_id)
        conf = Configurations.objects.get(school=school)
        # convert the raw data received to json
        data = json.loads(request.body)

        school_name = school.school_name

        # determine whether this test is marks based or grade based
        grade_based = False
        for key in data:
            test = ClassTest.objects.get(testresults__id=key)
            break  # because we can get the test object with the first key only

        # get the email of teacher. This is required for send_sms1
        t = test.teacher
        sender = t.email

        if test.grade_based:
            grade_based = True

        # iterate over json and save/update marks and also calculate highest and average marks
        present_count = 0
        highest_marks = 0.0
        mark_total = 0.0
        for key in data:
            tr = TestResults.objects.get(pk=key)

            if grade_based:
                tr.grade = data[key]
            else:
                tr.marks_obtained = float(data[key]['marks'])
                if float(data[key]['marks']) > highest_marks:
                    highest_marks = float(data[key]['marks'])
                    if highest_marks.is_integer():
                        highest_marks = int(highest_marks)
                if float(data[key]['marks']) != float(-1000):
                    mark_total += float(data[key]['marks'])
                    present_count += 1
                    average_marks = float(mark_total / present_count)
                    if average_marks.is_integer():
                        average_marks = int(average_marks)
                if test.test_type == 'term':
                    print('term test')
                    ttr = TermTestResult.objects.get(test_result=tr)
                    print(ttr)
                    ttr.periodic_test_marks = float(data[key]['pa'])
                    ttr.note_book_marks = float(data[key]['notebook'])
                    ttr.sub_enrich_marks = float(data[key]['subject_enrich'])
                    try:
                        ttr.save()
                        try:
                            action = 'Saved Term Test Results for ' + tr.student.fist_name \
                                     + ' ' + tr.student.last_name
                            action += ' ' + test.the_class.standard + '-' + test.section.section
                            action += ' ' + test.subject.subject_name
                            teacher = test.teacher.email
                            log_entry(teacher, action, 'Normal', True)
                        except Exception as e:
                            print('unable to create logbook entry')
                            print ('Exception 511-B from academics views.py %s %s' % (e.message, type(e)))
                    except Exception as e:
                        print('unable to save Term Test Marks')
                        print ('Exception 512-B from academics views.py %s %s' % (e.message, type(e)))
            try:
                tr.save()
                try:
                    action = 'Saved Test Results for ' + tr.student.fist_name + ' ' + tr.student.last_name
                    action += ' ' + test.the_class.standard + '-' + test.section.section
                    action += ' ' + test.subject.subject_name
                    teacher = test.teacher.email
                    log_entry(teacher, action, 'Normal', True)
                except Exception as e:
                    print('unable to create logbook entry')
                    print ('Exception 514 from academics views.py %s %s' % (e.message, type(e)))
            except Exception as e:
                print('unable to submit marks')
                print ('Exception 513 from academics views.py = %s (%s)' % (e.message, type(e)))

        # get the id of the associated test and mark it as complete
        test = ClassTest.objects.get(testresults__id=key)
        test.is_completed = True
        test.save()

        the_date = test.date_conducted
        d = str(the_date).split('-')[2]
        m = str(the_date).split('-')[1]
        y = str(the_date).split('-')[0]
        dmy_date = d + '/' + m + '/' + y

        # send marks to parents via sms
        threshold = 50
        initial = 0
        for key in data:

            # 11/21 - there seems to be some issue when we use threading with uwsgi in production. This loop can
            # execute for long thus sending same sms several times to the same parent. Hence we are implementing
            # threshold, which if exceeds, the function will return
            initial += 1
            print ('initial=' + str(initial))
            if initial > threshold:
                print ('exiting due to threshold was hit')
                response["status"] = "success"
                return JSONResponse(response, status=200)

            # print data[key]
            tr = TestResults.objects.get(pk=key)
            student = tr.student
            print (student)

            try:
                sub = test.subject
                action = 'Preapring to draft test result SMS for ' + student.parent.parent_name
                try:
                    log_entry(sender, action, 'Normal', True)
                except Exception as e:
                    print('unable to create logbook entry')
                    print ('Exception 515 from academics views.py %s %s' % (e.message, type(e)))
                message = 'Dear ' + student.parent.parent_name
                if grade_based:
                    message += ', Grade secured by '
                else:
                    message += ', Marks secured by '

                # 17/02/17 we are looking to use student first name in messages. However, some schools store entire
                # name as first name. This need to be checke and split first name if entire name is stored as first name
                the_name = student.fist_name
                if ' ' in student.fist_name:
                    (f_name, l_name) = the_name.split(' ')
                else:
                    f_name = the_name
                message += f_name + ' in '
                message += sub.subject_name + ' test on ' + dmy_date + ': '
                if grade_based:
                    if data[key]['marks'] == '-1000.00' or data[key]['marks'] == '-1000':
                        message += 'ABSENT'
                    else:
                        message +=  tr.grade + ' Grade'
                else:
                    if data[key]['marks'] == '-1000.00' or data[key]['marks'] == '-1000':
                        message += 'ABSENT'
                    else:
                        marks = float(tr.marks_obtained)
                        if marks.is_integer():
                            marks = int(marks)
                        message += str(marks) + '/' + str(int(test.max_marks))

                    # 24/09/2017 - if this is a term test, we need to include marks for Periodic Assessment,
                    # Notebook submission, and Subject Enrichment
                    if test.test_type == 'term':
                        ttr = TermTestResult.objects.get(test_result=tr)
                        message += '. Periodic Test: ' + str(ttr.periodic_test_marks) + '/10, '
                        message += 'Notebook Submission: ' + str(ttr.note_book_marks) + '/5, '
                        message += 'Subject Enrichment: ' + str(ttr.sub_enrich_marks) + '/5'

                if not grade_based:
                    # 04/12/2016 - some schools don't want to include max and average marks in the sms
                    if conf.include_max_avg_marks:
                        message += '. Highest marks: ' + str(highest_marks)
                        message += ' & Avg marks: ' + str(round(average_marks))
                message += ". Regards, " + school_name

                try:
                    action = 'Test Marks SMS Drafted for ' + student.parent.parent_name
                    log_entry(sender, action, 'Normal', True)
                except Exception as e:
                    print('unable to create logbook entry')
                    print ('Exception 516 from academics views.py %s %s' % (e.message, type(e)))

                # print message

                p = student.parent
                m1 = p.parent_mobile1
                message_list[m1] = message
                m2 = p.parent_mobile2

                # 11/20 - we may need to send sms for about 40-50 students, which can be time consumeing.
                # Hence we use thread

                # 11/21 afrer several trial runs it is observed that on server where we use uwsgi, implemenation
                # threading results in sending same sms several times thsus increasing costs. This may be due to the
                # face that uwsgi spawns its own thread and then our thread gets mixed with uwsgin thread. Hence, turn
                # off threading till some solution is found

                result = Queue.Queue()
                message_type = 'Test Marks'

                if conf.send_marks_sms:
                    sms.send_sms1(school, sender, m1, message, message_type)
                    try:
                        action = 'Test Result SMS sent to ' + p.parent_name + ' (' + p.parent_mobile1 + ')'
                        log_entry(sender, action, 'Normal', True)
                    except Exception as e:
                        print('unable to create logbook entry')
                        print ('Exception 516 from academics views.py %s %s' % (e.message, type(e)))
                    if conf.send_absence_sms_both_to_parent:
                        if m2 != '':
                            sms.send_sms1(school, sender, m2, message, message_type)
                            try:
                                action = 'Test Result SMS sent to ' + p.parent_name + ' (' + p.parent_mobile2 + ')'
                                log_entry(sender, action, 'Normal', True)
                            except Exception as e:
                                print('unable to create logbook entry')
                                print ('Exception 517 from academics views.py %s %s' % (e.message, type(e)))

            except Exception as e1:
                print ('unable send sms for ' + student.fist_name + ' ' + student.last_name)
                print ('Exception 518 from academics viws.py = %s (%s)' % (e1.message, type(e1)))

        count = 0
        for mobile in message_list:
            print (mobile)
            print (message_list[mobile])
            count += 1
            print (count)
        t2 = datetime.datetime.now()
        print ('execution took ' + str(t2 - t1))
        response["status"] = "success"
        return JSONResponse(response, status=200)


@csrf_exempt
def get_working_days1(request):
    month_dict = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }

    response = {
    }

    if request.method == 'GET':

        y = request.GET.get('year')
        print (y)
        mo = request.GET.get('month')
        m = month_dict[mo]

        school_id = request.GET.get('school_id')
        cl = request.GET.get('class')
        the_section = request.GET.get('section')
        the_subject = request.GET.get('subject')

        school = School.objects.get(id=school_id)
        try:
            school = School.objects.get(id=school_id)
            configuration = Configurations.objects.get(school=school)
            session_start_month = configuration.session_start_month
        except Exception as e:
            print ('unable to fetch the session_start_month for school with id:  ' + school_id)
            print ('Exception 1 from academics views.py = %s (%s)' % (e.message, type(e)))

        the_class = Class.objects.get(school=school, standard=cl)
        section = Section.objects.get(school=school, section=the_section)

        # 11/08/2016 earlier the summary was based on the main only but now they can be for any specific subject
        # main = Subject.objects.get(subject_name='Main')
        subject = Subject.objects.get(school=school, subject_name=the_subject)

        if y != 'till_date':
            print ('calculating working days for the month ' + mo + ' of year ' + y)
            try:
                query = AttendanceTaken.objects.filter(date__month=m, date__year=y, subject=subject,
                                                       the_class=the_class, section=section)
                total_days = query.count()
                print ('total days found = ' + str(total_days))

                response['working_days'] = total_days
                return JSONResponse(response, status=200)
            except Exception as e:
                print ('unable to fetch the number of days for ' + str(m) + '/' + str(y))
                print ('Exception 2 from academics views.py = %s (%s)' % (e.message, type(e)))
                return JSONResponse('Failed', status=201)
        else:
            # logic: if current month is less than session_start_month,
            # this means that the session started last year. So we need to add the working day for each month from
            # session start month till dec for last year and jan till current-1  month for current year.
            now = datetime.datetime.now()
            days_till_last_month = 0
            if now.month < session_start_month:
                for m in range(session_start_month,
                               12 + 1):  # 12+1, because loop executes for 1 time less than max index
                    try:
                        query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year - 1,
                                                               subject=subject, the_class=the_class,
                                                               section=section)
                        total_days = query.count()
                        print ('days in ' + str(m) + '/' + str(now.year - 1) + '=' + str(total_days))
                        days_till_last_month += total_days
                    except Exception as e:
                        print
                        print ('unable to fetch the number of days for ' + str(m) + '/' + str(now.year - 1))
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        return JSONResponse('Failed', status=404)
                for m in range(1, now.month + 1):
                    try:
                        query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year, subject=subject,
                                                               the_class=the_class, section=section)
                        total_days = query.count()
                        print ('days in ' + str(m) + '/' + str(now.year - 1) + '=' + str(total_days))
                        days_till_last_month += total_days
                    except Exception as e:
                        print ('unable to fetch the number of days for ' + str(m) + '/' + str(now.year))
                        print ('Exception3 from academics views.py = %s (%s)' % (e.message, type(e)))
                        return JSONResponse('Failed', status=404)
            # if current month is higher than the session_start_month then we need to add the working days
            # session start month till current-1 month
            else:
                for m in range(session_start_month, now.month + 1):
                    try:
                        query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year, subject=subject,
                                                               the_class=the_class, section=section)
                        total_days = query.count()
                        print ('days in ' + str(m) + '/' + str(now.year - 1) + '=' + str(total_days))
                        days_till_last_month += total_days
                    except Exception as e:
                        print ('unable to fetch the number of days for ' + str(m) + '/' + str(now.year))
                        print ('Exception4 from academics views.py = %s (%s)' % (e.message, type(e)))
                        return JSONResponse('Failed', status=404)
            response['working_days'] = days_till_last_month
            return JSONResponse(response, status=200)
    print (datetime.datetime.now())
    return HttpResponse('OK')


def get_attendance_summary(request):
    print ('request for attendance summary started at=')
    print (datetime.datetime.now())
    month_dict = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }

    dict_attendance_summary = {

    }

    response_array = []

    if request.method == 'GET':
        school_id = request.GET.get('school_id')
        try:
            school = School.objects.get(id=school_id)
            configuration = Configurations.objects.get(school=school)
            session_start_month = configuration.session_start_month
        except Exception as e:
            print ('unable to fetch the session_start_month for school with id:  ' + school_id)
            print ('Exception6 from academics views.py = %s (%s)' % (e.message, type(e)))

        c = request.GET.get('class')
        sec = request.GET.get('section')
        sub = request.GET.get('subject')
        m = request.GET.get('month')
        y = request.GET.get('year')
        print ('while in attendance summary, year from request=' + y)

        # get the number of working days for the duration mentioned in request (for a specific month or till date)
        # we are re-using the view get_working_days. We need to simulate an HTTP GET request to use the view
        factory = RequestFactory()

        request = factory.get('/academics/get_working_days1/?school_id=' + school_id + '&year=' + y +
                              '&month=' + m + '&class=' + c + '&section=' + sec + '&subject=' + sub)

        # the response contains newlines and Content type information. Hence it cannot be converted to json as it is.
        # we need to remove newlines and content type in order to convert it to json
        response = str(get_working_days1(request))
        data = response.replace('Content-Type: application/json', '')

        data = data.strip('\r\n')
        json_data = json.loads(data)
        working_days = json_data['working_days']
        print (working_days)

        print ('working days=' + str(json_data['working_days']))

        # get the list of students for the given class, section,
        q = Student.objects.filter(school=school, current_section__section=sec,
                                   current_class__standard=c, active_status=True)
        subject = Subject.objects.get(school=school, subject_name=sub)
        # for this subject and duration get the number of absent days for each student one by one. Also, keep
        # on building the json to be returned
        for s in q:
            if y != 'till_date':
                try:
                    query = Attendance.objects.filter \
                        (student=s, subject=subject, date__month=month_dict[m], date__year=y)
                    absent_days = query.count()
                except Exception as e:
                    print ('Exception 7 from academics views.py = %s (%s)' % (e.message, type(e)))
            else:
                # logic: if current month is less than session_start_month,
                # this means that the session started last year. So we need to add the working day for each month from
                # session start month till dec for last year and jan till current-1  month for current year.
                absent_days = 0
                now = datetime.datetime.now()

                if now.month < session_start_month:
                    for m in range(session_start_month,
                                   12 + 1):  # 12+1, because loop executes for 1 time less than max index
                        try:
                            query = Attendance.objects.filter \
                                (student=s, subject=subject, date__month=m, date__year=now.year - 1)
                            absent_days += query.count()
                            print ('absent days for ' + str(m) + '/' + str(now.year - 1) + '=' + str(query.count()))
                        except Exception as e:
                            print ('unable to fetch absent days for ' + str(m) + '/' + str(now.year - 1))
                            print ('Exception = %s (%s)' % (e.message, type(e)))
                            return JSONResponse('Failed', status=404)
                    for m in range(1, now.month + 1):
                        try:
                            query = Attendance.objects.filter \
                                (student=s, subject=subject, date__month=m, date__year=now.year)
                            absent_days += query.count()
                            print ('absent days for ' + str(m) + '/' + str(now.year) + '=' + str(query.count()))
                        except Exception as e:
                            print ('unable to fetch absent days for ' + str(m) + '/' + str(now.year))
                            print ('Exception8 from academics views.py = %s (%s)' % (e.message, type(e)))
                            return JSONResponse('Failed', status=404)
                # if current month is higher than the session_start_month then we need to add the working days
                # session start month till current-1 month
                else:
                    for m in range(session_start_month, now.month + 1):
                        try:
                            query = Attendance.objects.filter(student=s, subject=subject,
                                                              date__month=m, date__year=now.year)
                            absent_days += query.count()

                            print ('absent days for ' + str(m) + '/' + str(now.year) + '=' + str(query.count()))
                        except Exception as e:
                            print ('unable to fetch absent days for ' + str(m) + '/' + str(now.year))
                            print ('Exception9 from academics views.py = %s (%s)' % (e.message, type(e)))
                            return JSONResponse('Failed', status=404)
            # response['working_days'] = days_till_last_month
            print ('absent days=' + str(absent_days))
            present_days = working_days - absent_days
            # calculate the % of present days
            if int(working_days) < 1:
                dict_attendance_summary['percentage'] = 'N/A'
            else:
                present_perc = int(round((float(present_days) / float(working_days)) * 100, 0))
                dict_attendance_summary['percentage'] = str(present_perc) + '%'

            print ('present days=' + str(present_days))

            dict_attendance_summary['name'] = s.fist_name + ' ' + s.last_name
            dict_attendance_summary['roll_number'] = s.roll_number

            dict_attendance_summary['present_days'] = str(present_days)
            d = dict(dict_attendance_summary)
            response_array.append(d)

        print (response_array.__len__())

        print ('request for attendance summary finished at=')
        print (datetime.datetime.now())
        return JSONResponse(response_array, status=200)


@csrf_exempt
def delete_test(request, test_id):
    response = {

    }
    if request.method == 'DELETE':
        try:
            t = ClassTest.objects.get(pk=int(test_id))
            teacher = t.teacher.email
            t.delete()
            try:
                action = 'Deleted test '  + t.the_class.standard + '-' + t.section.section
                action += ', Subject' + t.subject.subject_name
                log_entry(teacher, action, 'Normal', True)
            except Exception as e:
                print('unable to create logbook entry')
                print ('Exception 521 from academics views.py %s %s' % (e.message, type(e)))
            response["status"] = "success"
            return JSONResponse(response, status=200)
        except Exception as e:
            response["status"] = "failed"
            print('Unable to delete test with id=' + test_id)
            print ('Exception 11 from academics views.py = %s (%s)' % (e.message, type(e)))
            return JSONResponse(response, status=404)


@csrf_exempt
def delete_hw(request, hw_id):
    response = {

    }
    if request.method == 'DELETE':
        try:
            t = HW.objects.get(pk=int(hw_id))
            teacher = t.teacher
            t.delete()
            try:
                action = 'Deleted HW '  + t.the_class + '-' + t.section + ', Subject: ' + t.subject
                log_entry(teacher, action, 'Normal', True)
            except Exception as e:
                print('unable to create logbook entry')
                print ('Exception 522 from academics views.py %s %s' % (e.message, type(e)))
            response["status"] = "success"
            return JSONResponse(response, status=200)
        except Exception as e:
            response["status"] = "failed"
            print('Unable to delete HW with id=' + hw_id)
            print ('Exception 10 from academics views.py = %s (%s)' % (e.message, type(e)))
            return JSONResponse(response, status=404)