import ast
import statistics

from django.shortcuts import render
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from authentication.views import JSONResponse

from setup.models import School
from student.models import Student
from academics.models import Class, Section, Subject, Exam, ClassTest, TestResults, TermTestResult
from exam.models import Wing
from .models import SubjectAnalysis, SubjectHighestAverage


# Create your views here.


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class GenerateSubAnalysis(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)

        classes = Class.objects.filter(school=school)
        sections = Section.objects.filter(school=school)
        exams = Exam.objects.filter(school=school, exam_type='term')
        print('exams = ')
        print(exams)

        try:
            jc = Wing.objects.get(school=school, wing='junior_classes')
            junior_classes = ast.literal_eval(jc.classes)
            print('junior_classes for %s are: ' % school)
            print(junior_classes)
        except Exception as e:
            print('exception 26102019-Z from analytics views.py %s %s' % (e.message, type(e)))
            print('junior_classes not defined for %s' % school)
            junior_classes = ['not defined']

        try:
            mc = Wing.objects.get(school=school, wing='middle_classes')
            print('raw middle_classes retrieved for %s: %s. Will be converted to proper string now' %
                  (school, mc.classes))
            middle_classes = ast.literal_eval(mc.classes)
            print('middle_classes for %s are: ' % school)
            print(middle_classes)
        except Exception as e:
            print('exception 26102019-Y from analytics views.py %s %s' % (e.message, type(e)))
            print('middle_classes not defined for %s' % school)
            middle_classes = ['not defined']

        try:
            nt = Wing.objects.get(school=school, wing='ninth_tenth')
            ninth_tenth = ast.literal_eval(nt.classes)
            print('ninth_tenth for %s are: ' % school)
            print(ninth_tenth)
        except Exception as e:
            print('exception 26102019-X from analytics.py %s %s' % (e.message, type(e)))
            print('ninth_tenth not defined for %s' % school)
            ninth_tenth = ['not defined']

        try:
            hc = Wing.objects.get(school=school, wing='higher_classes')
            higher_classes = ast.literal_eval(hc.classes)
            print('higher_classes for %s are: ' % school)
            print(higher_classes)
        except Exception as e:
            print('exception 26102019-W from analytics.py %s %s' % (e.message, type(e)))
            print('higher_classes not defined for %s' % school)
            higher_classes = ['not defined']
        for exam in exams:
            print('dealing with exam %s' % exam)
            for a_class in classes:
                for section in sections:
                    # first get the highest and average for each subject taught in this class
                    tests = ClassTest.objects.filter(exam=exam, the_class=a_class, section=section)
                    print('tests under %s for class %s-%s' % (exam, a_class, section))
                    print(tests)
                    for test in tests:
                        marks_array = []
                        subject = test.subject

                        print('finding the highest and calculating average marks in %s class %s-%s' %
                              (subject, a_class, section))
                        results = TestResults.objects.filter(class_test=test, marks_obtained__gte=0.0)
                        total = 0.0
                        for result in results:
                            total += float(result.marks_obtained)
                            print('total just from theory exam = %.2f' % total)
                            term_results = TermTestResult.objects.get(test_result=result)
                            print('term_results = ')
                            print(term_results)

                            if (a_class.standard in middle_classes) or (a_class in ninth_tenth):
                                pa_marks = float(term_results.periodic_test_marks)
                                mult_asses = float(term_results.multi_asses_marks)
                                notebook = float(term_results.note_book_marks)
                                sub_enrich = float(term_results.sub_enrich_marks)
                                total += pa_marks + mult_asses + notebook + sub_enrich
                                print('total after adding other components = %.2f' % total)

                            if a_class.standard in higher_classes:
                                prac_marks = float(term_results.prac_marks)
                                total += prac_marks
                                print('total after adding other components = %.2f' % total)

                            if total > 0.0:
                                marks_array.append(total)
                                total = 0.0
                        print(marks_array)
                        average = statistics.mean(marks_array)
                        highest = max(marks_array)

                        try:
                            sub_high_avg = SubjectHighestAverage.objects.get(exam=exam, the_class=a_class,
                                                                             section=section, subject=subject)
                            sub_high_avg.average = average
                            sub_high_avg.highest = highest
                            sub_high_avg.save()
                            print('updated average highest for %s class %s-%s' % (subject, a_class, section))
                        except Exception as e:
                            print('exception 26102019-E from analytics views.py %s %s' % (e.message, type(e)))
                            print('average & highest not yet determined for %s class %s-%s. Doing now...' %
                                  (subject, a_class, section))
                            sub_high_avg = SubjectHighestAverage(exam=exam, the_class=a_class,
                                                                 section=section, subject=subject)
                            sub_high_avg.average = average
                            sub_high_avg.highest = highest
                            sub_high_avg.save()
                            print('created average highest for %s class %s-%s' % (subject, a_class, section))

        print('generating analytics for %s-%s' % (a_class, section))
        students = Student.objects.filter(school=school)
        for student in students:
            for exam in exams:
                tests = ClassTest.objects.filter(exam=exam, the_class=student.current_class,
                                                 section=student.current_section)
                print(tests)
                for test in tests:
                    subject = test.subject
                    try:
                        test_result = TestResults.objects.get(class_test=test, student=student)
                        marks = float(test_result.marks_obtained)

                        term_results = TermTestResult.objects.get(test_result=test_result)
                        if student.current_class.standard in middle_classes or \
                                student.current_class.standard in ninth_tenth:
                            pa_marks = float(term_results.periodic_test_marks)
                            mult_asses = float(term_results.multi_asses_marks)
                            notebook = float(term_results.note_book_marks)
                            sub_enrich = float(term_results.sub_enrich_marks)
                            total_marks = marks + pa_marks + mult_asses
                            total_marks += notebook + sub_enrich

                        if student.current_class.standard in higher_classes:
                            prac_marks = float(term_results.prac_marks)
                            total_marks = marks + prac_marks

                        if total_marks < 0.0:
                            total_marks = 0.0

                        print('total marks for %s in %s of %s-%s = %.2f' %
                              (student, subject, student.current_class,
                               student.current_section, total_marks))
                        try:
                            highest_average = SubjectHighestAverage.objects.get(exam=exam,
                                                                                the_class=student.current_class,
                                                                                section=student.current_section,
                                                                                subject=subject)
                            highest = highest_average.highest
                            average = highest_average.average

                            # get the highest and average marks in this subject for this exam
                            try:
                                analytics = SubjectAnalysis.objects.get(student=student, exam=exam,
                                                                        subject=subject)
                                analytics.marks = total_marks
                                analytics.highest = highest
                                analytics.average = average
                                analytics.save()
                                print('updated highest & average for %s in exam %s' % (subject, exam))
                            except Exception as e:
                                print('exception 26102019-B from analytics views.py %s %s' %
                                      (e.message, type(e)))
                                print('analytics for %s in %s for %s-%s not yet created. Creating now..' %
                                      (student, subject, student.current_class, student.current_section))
                                analytics = SubjectAnalysis(student=student, exam=exam, subject=subject)
                                analytics.marks = total_marks
                                analytics.highest = highest
                                analytics.average = average
                                analytics.save()
                                print('created highest & average for %s in exam %s' % (subject, exam))
                        except Exception as e:
                            print('exception 26102019-C from analytics views.py %s %s' %
                                  (e.message, type(e)))
                            print('highest & average marks not yet determined for %s in exam %s' %
                                  (subject, exam))

                    except Exception as e:
                        print('exception 27102019-A from analytics.py %s %s' % (e.message, type(e)))
                        print('failed to retrieve test/term results for %s in %s %s-%s' %
                              (student, subject, student.current_class, student.current_section))
        context_dict['outcome'] = 'success'
        return JSONResponse(context_dict, status=200)
