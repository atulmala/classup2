import json
from datetime import date
from decimal import Decimal

from django.http import HttpResponse
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.renderers import JSONRenderer

from exam.models import HigherClassMapping, Wing
from setup.models import School
from academics.models import Class, Section, Subject, Exam, ClassTest, TestResults, TermTestResult, ThirdLang
from exam.views import get_wings
from student.models import Student
from teacher.models import Teacher

from academics.serializers import TestSerializer


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class JSONResponse(HttpResponse):
    """
    an HttpResponse that renders its contents to JSON
    """

    def __init__(self, data, **kwargs):
        print ('from JSONResponse...')
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class TestList(generics.ListAPIView):
    serializer_class = TestSerializer

    def get_queryset(self):
        school_id = self.request.query_params.get('school_id')
        school = School.objects.get(id=school_id)
        for_whom = self.request.query_params.get('for_whom')
        if for_whom == 'teacher':
            print('test list for a teacher to be retrieved')
            t = self.request.query_params.get('teacher')
            print(t)
            teacher = Teacher.objects.get(school=school, email=t)
            q = ClassTest.objects.filter(teacher=teacher).order_by('-date_conducted')
            return q


class GetWings(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        context_dict = {}
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        wings = Wing.objects.filter(school=school)
        for a_wing in wings:
            context_dict[a_wing.wing] = a_wing.classes
        return JSONResponse(context_dict, status=200)


class ScheduleTest(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {'header': 'Create Test'}
        try:
            data = json.loads(request.body)
            print(data)
            school_id = data['school_id']
            school = School.objects.get(id=school_id)
            t = data['teacher']
            teacher = Teacher.objects.get(email=t)
            exam_id = data['exam_id']
            exam = Exam.objects.get(pk=exam_id)
            cls = data['the_class']
            the_class = Class.objects.get(school=school, standard=cls)
            sec = data['section']
            section = Section.objects.get(school=school, section=sec)
            sub = data['subject']
            subject = Subject.objects.get(school=school, subject_name=sub)
            the_date = data['date']
            y, m, d = the_date.split('-')
            test_date = date(int(y), int(m), int(d))
            grade_based = data['grade_based']
            max_marks = data['max_marks']
            pass_marks = data['passing_marks']
            syllabus = data['syllabus']
        except Exception as e:
            print('exception 20112019-A from exam test_management.py %s %s' % (e.message, type(e)))
            print('failure in decoding the json')
            context_dict['outcome'] = 'failure in decoding json'
            return JSONResponse(context_dict, status=201)

        wings = get_wings(school)
        junior_classes = wings['junior_classes']
        middle_classes = wings['middle_classes']
        ninth_tenth = wings['ninth_tenth']
        higher_classes = wings['higher_classes']

        # check if this test has already been created by some other teacher
        q = ClassTest.objects.filter(exam=exam, the_class=the_class, section=section, subject=subject)
        print (q.count())
        if q.count() > 0:
            teacher = q[:1].get().teacher
            name = '%s %s' % (teacher.first_name, teacher.last_name)
            outcome = ('test for %s %s %s-%s already created by %s. Hence not creating' %
                       (exam.title, sub, the_class, section, name))
            print(outcome)
            context_dict['outcome'] = outcome
            return JSONResponse(context_dict, status=201)

        print('test for %s %s %s-%s does not exist. Hence  creating' % (exam.title, sub,
                                                                        the_class.standard, section.section))
        try:
            test = ClassTest(date_conducted=test_date)
            test.exam = exam
            test.the_class = the_class
            test.section = section
            test.subject = subject
            test.teacher = teacher
            test.max_marks = float(max_marks)  # max_marks and pass_marks are passed as strings
            test.passing_marks = float(pass_marks)

            # 24/12/2017 for class XI & XII max marks & passing marks are different for every subject.
            # Hence let us keep max marks = 100 and passing marks = 0. School will analyze in the result sheets
            if the_class in higher_classes:
                if exam.exam_type == 'term':
                    test.max_marks = 100.0
                    test.passing_marks = 0.0

            test.test_type = exam.exam_type

            if grade_based == 'true' or grade_based:
                test.grade_based = True
            else:
                test.grade_based = False

            test.syllabus = syllabus
            test.is_completed = False
            test.save()
            print('successfully scheduled test for %s class %s-%s for %s' %
                  (subject, the_class, section, exam))
        except Exception as e:
            print('exception 20112019-B from exam test_management.py %s %s' % (e.message, type(e)))
            outcome = 'failed to create test for %s class %s-%s for %s' % (subject, the_class, section, exam)
            print(outcome)
            context_dict['outcome'] = outcome
            return JSONResponse(context_dict, status=201)

        # test is created, now create result for each student
        student_list = Student.objects.filter(school=school, current_section=section, current_class=the_class,
                                              active_status=True).order_by('fist_name', 'last_name')
        for student in student_list:
            # 15/11/2017 - for higher classes (XI & XII) we need to look into the student subject mapping
            if the_class.standard in higher_classes:
                print ('test is for higher class %s. Hence, mapping will be considered' % the_class)
                try:
                    mapping = HigherClassMapping.objects.get(student=student, subject=subject)
                    if mapping:
                        test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                                  student=student, marks_obtained=-5000.00, grade='')
                        test_result.save()
                        print ('test results successfully created for %s' % (student))

                        # 24/12/2017 in case of higher classes, practical marks need to be initialized
                        if exam.exam_type == 'term':
                            print('term test for higher class. Hence provision for practical marks')
                            term_test_result = TermTestResult(test_result=test_result, prac_marks=-5000.0)
                            term_test_result.save()
                            print ('term test results successfully created for %s' % (student))
                except Exception as e:
                    print ('mapping does not exist between subject %s and %s' % (sub, student))
                    print ('exception 20112019-C from exam test_management.py %s %s' % (e.message, type(e)))
            else:
                # 06/11/2017 if the subject is third language or elective subject (class XI & XII),
                #  we need to filter students
                check_for_term = False
                if (subject.subject_type == 'Third Language') or \
                        ((the_class in ninth_tenth) and (subject.subject_name == 'Hindi')):
                    print ('this is a second/third language. Hence test results will be created for selected students')
                    try:
                        third_lang = ThirdLang.objects.get(third_lang=subject, student=student)
                        print ('%s has chosen %s as second/third language' % (student.fist_name, subject))
                        test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                                  student=third_lang.student, marks_obtained=-5000.00, grade='')
                        try:
                            test_result.save()
                            print ('test results successfully created for %s' % student)
                            check_for_term = True
                        except Exception as e:
                            print ('failed to create test results for %s' % student)
                            print ('Exception 20112019-D from exam test_management.py = %s (%s)' %
                                   (e.message, type(e)))
                            context_dict['outcome'] = 'Failed to create test'
                            return JSONResponse(context_dict, status=201)
                    except Exception as e:
                        print ('Exception 20112019-E from exam test_management.py %s %s' % (e.message, type(e)))
                        print ('%s has not chosen %s as third language' % (student, subject))
                else:
                    print ('this is a regular subject. Hence test results will be created for all students')
                    test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                              student=student, marks_obtained=-5000.00, grade='')
                    try:
                        test_result.save()
                        print ('test results successfully created for %s' % student)
                        check_for_term = True
                    except Exception as e:
                        print ('failed to create test results for %s' % student)
                        print ('Exception 20110219-F from exam test_management.py %s %s' % (e.message, type(e)))
                        context_dict['outcome'] = 'Failed to create test'
                        return JSONResponse(context_dict, status=201)

                if check_for_term:
                    if exam.exam_type == 'term':
                        if the_class.standard in middle_classes or the_class.standard in ninth_tenth:
                            # 01/02/2018 - If this is a second term test, ie the final exam for class
                            # V-VIII, then we need to auto fill the PA marks. The marks will be the
                            # average of all the unit test conducted between the first term test till now

                            term_tests = ClassTest.objects.filter(the_class=the_class, section=section, subject=subject,
                                                                  test_type='term').order_by('date_conducted')
                            print('term tests conducted so far for class %s-%s for subject %s' %
                                  (the_class, section, subject))
                            print(term_tests)
                            term1_test = term_tests[0]
                            term1_date = term1_test.date_conducted
                            if term_tests.count() > 1:  # this is the second term test
                                print('this is the second term (final) test for %s-%s subject %s' %
                                      (the_class, section, subject))
                                print('periodic assessments marks will be the average of unit tests')

                                print('previous first term test was conducted on ')
                                print(term1_date)

                                # get all the unit tests conducted between term1 & term2
                                unit_tests = ClassTest.objects.filter(the_class=the_class, section=section,
                                                                      subject=subject,
                                                                      date_conducted__gt=term1_date,
                                                                      date_conducted__lt=test_date)
                            else:
                                # get all the unit tests conducted before term1
                                unit_tests = ClassTest.objects.filter(the_class=the_class, section=section,
                                                                      subject=subject, date_conducted__lt=term1_date)
                            print('%i unit tests have been conducted for in class %s-%s for %s' %
                                  (unit_tests.count(), the_class, section, subject))
                            print(unit_tests)
                            marks_array = []
                            for ut in unit_tests:
                                ut_result = TestResults.objects.get(class_test=ut, student=student)

                                # 23/09/2019 - as per new CBSE ut_marks should be out of 5.
                                # Another 5 marks component would be Multiple Assesment
                                # ut_marks = (ut_result.marks_obtained / ut.max_marks) * Decimal(10.0)
                                ut_marks = (ut_result.marks_obtained / ut.max_marks) * Decimal(5.0)
                                # 13/03/2018 - if the student was absent, then marks will be < 0
                                if ut_marks < 0.0:
                                    print('marks = %f' % ut_marks)
                                    ut_marks = 0.0
                                else:
                                    marks_array.append(ut_marks)
                                print('marks_array = ')
                                print(marks_array)
                            marks_array.sort(reverse=True)
                            try:
                                # average of best of two tests
                                pa_marks = (marks_array[0] + marks_array[1]) / Decimal(2.0)
                                print('average of best of two tests = %f' % pa_marks)
                            except Exception as e:
                                print('looks only one cycle test has been conducted for %s in '
                                      'class %s-%s between Term1 & Terms 2' % (subject, the_class, section))
                                print('exception 11022018-Z from academics views.py %s %s' % (e.message, type(e)))
                                print('hence, taking the single unit/cycle test marks as PA marks')
                                try:
                                    pa_marks = marks_array[0]
                                except Exception as e:
                                    print('looks that marks for % s in %s have not been '
                                          'entered for any test' % (student.fist_name, sub))
                                    print('exception 13032018-A from academics views.py %s %s' % (e.message, type(e)))
                                    pa_marks = -5000.0

                            term_test_result = TermTestResult(test_result=test_result, periodic_test_marks=pa_marks,
                                                              multi_asses_marks=-5000.0, note_book_marks=-5000.0,
                                                              sub_enrich_marks=-5000.0)
                            term_test_result.save()
                        else:
                            print ('%s is a junior class. Hence not creating PA, Notbook Sub & Sub enrich' % the_class)
                        print (' test results successfully created for %s' % student)
        context_dict['outcome'] = 'Test successfully created'
        return JSONResponse(context_dict, status=200)




