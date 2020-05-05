import datetime as dt
import json
import os
import urllib2

import boto3
from datetime import date as today
from PIL import Image

import xlrd
import classup2.settings as settings

# Create your views here.
from django.http import HttpResponse
from google.cloud import storage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import generics
from rest_framework.authentication import BasicAuthentication

from academics.models import Class, Subject, Exam, Section, ClassTest, TestResults, ThirdLang
from authentication.views import CsrfExemptSessionAuthentication, JSONResponse
from exam.models import HigherClassMapping, Marksheet
from exam.views import get_wings
from online_test.models import OnlineTest, OnlineQuestion, StudentTestAttempt, StudentQuestion, AnswerSheets
from operations import sms
from setup.models import School, GlobalConf, Configurations
from student.models import Student
from teacher.models import Teacher

from .serializers import OnlineTestSerializer, OnlineQuestionSerializer


class MarkAttempted(generics.ListAPIView):
    def post(self, request, *args, **kwargs):
        student_id = self.kwargs['student_id']
        student = Student.objects.get(id=student_id)
        test_id = self.kwargs['test_id']
        online_test = OnlineTest.objects.get(id=test_id)

        context_dict = {}
        try:
            attempted = StudentTestAttempt.objects.get(student=student, online_test=online_test)
            print('attempt recorded')
        except Exception as e:
            print('exception 22042020-B from online_test viws.py %s %s' % (e.message, type(e)))
            print('recording attempt for the first time')
            attempted = StudentTestAttempt(student=student, online_test=online_test)
            attempted.save()

        return JSONResponse(context_dict, status=200)


class WhetherAttempted(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        student_id = self.kwargs['student_id']
        student = Student.objects.get(id=student_id)
        test_id = self.kwargs['test_id']
        online_test = OnlineTest.objects.get(id=test_id)

        context_dict = {}
        if StudentTestAttempt.objects.filter(student=student, online_test=online_test).exists():
            context_dict['attempted'] = 'true'
        else:
            context_dict['attempted'] = 'false'
        return JSONResponse(context_dict, status=200)


class GetOnlineQuestion(generics.ListAPIView):
    serializer_class = OnlineQuestionSerializer

    def get_queryset(self):
        test_id = self.kwargs['test_id']
        test = OnlineTest.objects.get(id=test_id)
        q = OnlineQuestion.objects.filter(test=test)
        return q


class GetOnlineTest(generics.ListAPIView):
    serializer_class = OnlineTestSerializer

    def get_queryset(self):
        user = self.kwargs['id']
        student = Student.objects.get(pk=user)
        the_class = student.current_class

        q = OnlineTest.objects.filter(the_class=the_class, date=today.today())
        return q


class CreateOnlineTest(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        print('resuest = ')
        print(request.FILES)
        context_dict = {

        }
        school_id = self.kwargs['school_id']
        school = School.objects.get(pk=school_id)
        print('school = %s' % school)

        try:
            print ('now starting to process the uploaded file for fee upload...')
            fileToProcess_handle = request.FILES['online_test.xlsx']
            print(fileToProcess_handle)
            fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read(),
                                               encoding_override="cp1252")
            sheet = fileToProcess.sheet_by_index(0)
            if sheet:
                print ('Successfully got hold of sheet!')
            row = 0
            for row1 in range(sheet.nrows):
                if row == 142:
                    break
                print('at the top of the loop, row = %i' % row)
                col = 1
                if row == 1:
                    print('A - row = %i' % row)
                    row += 1
                    continue
                if row == 0:
                    print('B - row = %i' % row)
                    standard = sheet.cell(row, col).value
                    print('standard = %s' % standard)
                    the_class = Class.objects.get(school=school, standard=standard)

                    col += 2
                    sub_name = sheet.cell(row, col).value
                    subject = Subject.objects.get(school=school, subject_name=sub_name)

                    col += 4
                    teacher_id = sheet.cell(row, col).value
                    print('teacher_id = %s' % teacher_id)
                    teacher = Teacher.objects.get(email=teacher_id)

                    col += 1
                    date = sheet.cell(row, col).value
                    try:
                        test_date = dt.datetime(*xlrd.xldate_as_tuple(date, fileToProcess.datemode))
                        print ('test date is in acceptable format')
                        print (test_date)
                    except Exception as e:
                        print ('problem with date')
                        print ('exception 18042020-H from online_test views.py %s %s ' % (e.message, type(e)))
                        continue

                    col += 1
                    exam_title = sheet.cell(row, col).value
                    try:
                        exam = Exam.objects.get(school=school, title=exam_title)
                    except Exception as e:
                        print('exception 01052020-A from online_test views.py %s %s' % (e.message, type(e)))

                    # create online test
                    try:
                        test = OnlineTest.objects.get(school=school, the_class=the_class,
                                                      subject=subject, exam=exam)
                        print ('online test for class %s subject %s exam %s has already been created' %
                               (the_class, subject, exam))
                        return JSONResponse(context_dict, status=200)
                    except Exception as e:
                        print('exception 28042020-A from online_test views.py %s %s' % (e.message, type(e)))
                        print ('online test for class %s subject %s exam %s has not been created' %
                               (the_class, subject, exam))
                        online_test = OnlineTest(school=school, the_class=the_class,
                                                 subject=subject, teacher=teacher, date=test_date, exam=exam)
                        online_test.save()
                        row += 1
                if row > 1:
                    print('C - row = %i' % row)
                    col = 1
                    try:
                        question = sheet.cell(row, col).value
                        row += 1
                        option_a = sheet.cell(row, col).value
                        row += 1
                        option_b = sheet.cell(row, col).value
                        row += 1
                        option_c = sheet.cell(row, col).value
                        row += 1
                        option_d = sheet.cell(row, col).value
                        row += 1
                        correct_option = sheet.cell(row, col).value
                    except Exception as e:
                        print('exception 01052020-X from online_test viws.py %s %s' % (e.message, type(e)))

                    online_question = OnlineQuestion(test=online_test, question=question,
                                                     option_a=option_a, option_b=option_b,
                                                     option_c=option_c, option_d=option_d,
                                                     correct_option=correct_option)
                    online_question.save()
                    row += 2
                    print('D - row = %i' % row)
        except Exception as e:
            print('exception 17042020-A from online_test views.py %s %s' % (e.message, type(e)))
            print('failed to create online test')

        # now create a manual test
        wings = get_wings(school)
        ninth_tenth = wings['ninth_tenth']
        higher_classes = wings['higher_classes']
        sections = Section.objects.filter(school=school)
        for section in sections:
            students = Student.objects.filter(current_class=the_class,
                                              current_section=section, active_status=True)
            if students.count() > 0:
                # check if this test has already been created by some other teacher
                q = ClassTest.objects.filter(exam=exam, the_class=the_class, section=section, subject=subject)
                if q.count() > 0:
                    teacher = q[:1].get().teacher
                    name = '%s %s' % (teacher.first_name, teacher.last_name)
                    outcome = ('test for %s %s %s-%s already created by %s. Hence not creating' %
                               (exam, subject, the_class, section, name))
                    print(outcome)
                    continue

                print('test for %s %s %s-%s does not exist. Hence  creating' % (exam, subject, the_class, section))
                try:
                    print(test_date)
                    print(teacher)
                    test = ClassTest(date_conducted=test_date, exam=exam, the_class=the_class, section=section,
                                     subject=subject, teacher=teacher, grade_based=False)
                    test.max_marks = float(20.00)  # max_marks and pass_marks are passed as strings
                    test.passing_marks = float(8.00)
                    test.save()
                    print('successfully scheduled test for %s class %s-%s for %s' %
                          (subject, the_class, section, exam))
                except Exception as e:
                    print('exception 28042020-B from online_test views.py %s %s' % (e.message, type(e)))
                    outcome = 'failed to create test for %s class %s-%s for %s' % (subject, the_class, section, exam)
                    print(outcome)
                    continue
                for student in students:
                    # for higher classes (XI & XII) we need to look into the student subject mapping
                    if the_class.standard in higher_classes:
                        print ('test is for higher class %s. Hence, mapping will be considered' % the_class)
                        try:
                            mapping = HigherClassMapping.objects.get(student=student, subject=subject)
                            if mapping:
                                test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                                          student=student, marks_obtained=-5000.00, grade='')
                                test_result.save()
                                print ('test results successfully created for %s' % (student))
                        except Exception as e:
                            print ('mapping does not exist between subject %s and %s' % (subject, student))
                            print ('exception 28042020-C from exam online_test view.py %s %s' % (e.message, type(e)))
                    else:
                        # 06/11/2017 if the subject is third language or elective subject (class XI & XII),
                        #  we need to filter students
                        if (subject.subject_type == 'Third Language') or \
                                ((the_class in ninth_tenth) and (subject.subject_name == 'Hindi')):
                            print (
                                'this is a second/third language. Hence test results will be created for selected students')
                            try:
                                third_lang = ThirdLang.objects.get(third_lang=subject, student=student)
                                print ('%s has chosen %s as second/third language' % (student.fist_name, subject))
                                test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                                          student=third_lang.student, marks_obtained=-5000.00, grade='')
                                try:
                                    test_result.save()
                                    print ('test results successfully created for %s' % student)
                                except Exception as e:
                                    print ('failed to create test results for %s' % student)
                                    print ('Exception 28042020-D from online_test views.py = %s (%s)' %
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
                            except Exception as e:
                                print ('failed to create test results for %s' % student)
                                print ('Exception 28042020-F from online_test views.py %s %s' % (e.message, type(e)))
                                context_dict['outcome'] = 'Failed to create test'
                                return JSONResponse(context_dict, status=201)
        return JSONResponse(context_dict, status=200)


class SubmitAnswer(generics.ListCreateAPIView):
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
            student_id = data[key]['student_id']
            student = Student.objects.get(id=student_id)

            question_id = data[key]['question_id']
            question = OnlineQuestion.objects.get(id=question_id)

            option_marked = data[key]['option_marked']

            student_question = StudentQuestion(student=student, question=question,
                                               answer_marked=option_marked)
            student_question.save()

        online_test = question.test
        try:
            attempt = StudentTestAttempt.objects.get(student=student, online_test=online_test)
            print('%s attempt has already been recorded' % student)
        except Exception as e:
            print('a good exception from online_test views.py %s %s' % (e.message, type(e)))
            print('%s attempt was not recorded' % student)
            attempt = StudentTestAttempt(student=student, online_test=online_test)
            attempt.save()

        context_dict['status'] = 'success'
        return JSONResponse(context_dict, status=200)


class GenerateAnswerSheet(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        # connect to AWS s3 bucket and
        try:
            session = boto3.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            s3 = session.resource('s3')
            print('s3 session established successfully')
        except Exception as e:
            print('exception 05052020-C from online_test views.py %s %s' % (e.message, type(e)))
            print('failed estable connections to AWS S3 storage')

        attempts = StudentTestAttempt.objects.all()

        for an_attempt in attempts:
            marks_obtained = 0
            student = an_attempt.student
            online_test = an_attempt.online_test
            questions = OnlineQuestion.objects.filter(test=online_test)
            for a_question in questions:
                try:
                    student_answer = StudentQuestion.objects.get(student=student, question=a_question)
                    option_marked = student_answer.answer_marked
                    correct_option = a_question.correct_option

                    if option_marked.strip() == correct_option.strip():
                        marks_obtained += 1
                except Exception as e:
                    print('exception 29042020-A from online_test views.py %s %s' % (e.message, type(e)))
                    print('could not retrieve student %s attempt for question %s' % (student, a_question.question))

            # update marks in corresponding offline test_date
            try:
                offline_test = ClassTest.objects.get(exam=online_test.exam, subject=online_test.subject,
                                                     the_class=online_test.the_class,
                                                     section=student.current_section)
                offline_result = TestResults.objects.get(student=student, class_test=offline_test)
                offline_result.marks_obtained = marks_obtained
                offline_result.save()
                print('successfully saved offline test marks for %s in %s class %s exam %s' %
                      (student, student.current_class, online_test.subject, online_test.exam))
            except Exception as e:
                print('exception 30042020-B from online_test view.py %s %s' % (e.message, type(e)))
                print('failed to fill offline test marks for %s in %s class %s exam %s' %
                      (student, student.current_class, online_test.subject, online_test.exam))

            try:
                answer_sheet = AnswerSheets.objects.get(student=student, online_test=online_test)
                print('answer sheet for %s for online test %s class %s has already been generated. Skipping' %
                      (student, online_test.subject, online_test.the_class))
                continue
            except Exception as e:
                print('answer sheet for %s for online test %s class %s has already not generated. Will do now' %
                      (student, online_test.subject, online_test.the_class))
            print('generating result for %s in online test class %s subject %s' %
                  (student, online_test.the_class, online_test.subject))

            pdf_name = 'online_test/%s_%s_answer_sheet_online_test_%s_class_%s.pdf' % \
                       (student.fist_name, str(student.id), student.current_class, online_test.subject)
            print('pdf_name = %s' % pdf_name)
            response = HttpResponse(content_type='application/pdf')
            content_disposition = ('attachment; filename= %s' % pdf_name)
            print (content_disposition)
            response['Content-Disposition'] = content_disposition
            print(response)
            c = canvas.Canvas(pdf_name, pagesize=A4, bottomup=1)

            font = 'Times-Bold'
            c.setFont(font, 12)
            font = 'Times-Bold'
            top = 750
            school = student.school
            ms = Marksheet.objects.get(school=school)
            title_start = ms.title_start
            c.drawString(title_start + 80, top, school.school_name)
            c.setFont(font, 8)
            top -= 10
            c.drawString(title_start + 100, top, 'Online Test Sheet')
            top -= 20
            c.drawString(60, top, 'Name: %s' % student)
            c.drawString(175, top, 'Class: %s' % student.current_class)
            c.drawString(260, top, 'Subject: %s (%s)' % (online_test.subject, online_test.exam))

            print('number of questions in this test: %d' % questions.count())
            c.drawString(400, top, 'Marks Obtained: %s / 20' % str(marks_obtained))

            top -= 20
            left = 100
            tick_mark = Image.open('online_test/correct.png')
            cross = Image.open('online_test/cross.png')

            print('number of questions in this test: %d' % questions.count())
            q_no = 1
            for a_question in questions:
                if q_no == 9 or q_no == 17:
                    top = 750
                    c.showPage()
                    c.setFont(font, 8)

                c.drawString(left, top, 'Q %s - %s' % (str(q_no), a_question.question))
                top -= 15
                c.drawString(left, top, 'A.   %s' % a_question.option_a)
                top -= 10
                c.drawString(left, top, 'B.   %s' % a_question.option_b)
                top -= 10
                c.drawString(left, top, 'C.   %s' % a_question.option_c)
                top -= 10
                c.drawString(left, top, 'D.   %s' % a_question.option_d)
                top -= 15
                c.drawString(left, top, 'Correct Option:  %s' % a_question.correct_option)
                try:
                    student_answer = StudentQuestion.objects.get(student=student, question=a_question)
                    option_marked = student_answer.answer_marked
                    correct_option = a_question.correct_option
                    print('for question %d, %s has marked %s and correct option is %s' %
                          (q_no, student, student_answer.answer_marked, a_question.correct_option))
                    c.drawString(left + 100, top, 'Your Answer: %s' % student_answer.answer_marked)

                    if option_marked.strip() == correct_option.strip():
                        print('%s has marked question: %d correct.' % (student, q_no))
                        c.drawInlineImage(tick_mark, left - 30, top + 20, width=15, height=15)
                        c.drawString(left + 220, top, 'Marks: 2')
                    else:
                        print('%s has marked question: %d wrong.' % (student, q_no))
                        c.drawInlineImage(cross, left - 30, top + 20, width=15, height=15)
                        c.drawString(left + 220, top, 'Marks: 0')
                except Exception as e:
                    print('exception 29042020-A from online_test views.py %s %s' % (e.message, type(e)))
                    print('could not retrieve student %s attempt for question %s' % (student, a_question.question))

                top -= 20
                q_no += 1

            context_dict = {
                'marks_obtained': marks_obtained
            }
            c.save()

            print('uploading %s online test %s class %s to AWS S3 Storage' %
                  (student, online_test.subject, online_test.the_class))
            try:
                s3.meta.client.upload_file(Filename=pdf_name, Bucket='classup2', Key='classup2/%s' % pdf_name)
                print('uploaded')
            except Exception as e:
                print('exception 05052020-B from online_test views.py %s %s' % (e.message, type(e)))
                print('failed to upload answer sheet for %s to AWS S3 storage' % student)

            print('will now try to generate short link')
            long_link = 'https://classup2.s3.us-east-2.amazonaws.com/classup2/%s' % pdf_name
            print('long link: %s' % long_link)
            # prepare short link
            global_conf = GlobalConf.objects.get(pk=1)
            key = global_conf.short_link_api
            url = 'https://cutt.ly/api/api.php?'
            url += 'key=%s&short=%s' % (key, long_link)
            print('url for generating short link = %s' % url)
            try:
                response = urllib2.urlopen(url)
                print('response for generating short link = %s' % response)
                outcome = json.loads(response.read())
                print('ouctome = ')
                print(outcome)
                status = outcome['url']['status']
                print('status = %i' % status)
                if status == 7:
                    short_link = outcome['url']['shortLink']
                    print('short_lint = %s' % short_link)
            except Exception as e:
                print('exception 30042020-A from online_test views.py %s %s' % (e.message, type(e)))
                print('failed to generate short link  for the lesson doc uploaded by %s')
                short_link = long_link

            try:
                answer_sheet = AnswerSheets.objects.get(student=student, online_test=online_test)
                print('answer sheet for %s of class %s-%s in for the online test of %s exists. Now updated' %
                      (student, student.current_class, student.current_section, online_test.subject))
                answer_sheet.link = short_link
            except Exception as e:
                print('exception 05052020-A from online_test views.py %s %s' % (e.message, type(e)))
                print('answer sheet for %s of class %s-%s in for the online test of %s creating for the first time.' %
                      (student, student.current_class, student.current_section, online_test.subject))
                answer_sheet = AnswerSheets(student=student, online_test=online_test)
                answer_sheet.link = short_link
            answer_sheet.save()
            os.remove(pdf_name)
            # return response

        return JSONResponse(context_dict, status=200)


class ShareAnswerSheet(generics.ListAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        answer_sheets = AnswerSheets.objects.all()
        for a_sheet in answer_sheets:
            if not a_sheet.shared:
                message = 'Dear %s, answer sheet of %s online test attached. link:  %s' % \
                          (a_sheet.student, a_sheet.online_test.subject, a_sheet.link)
                print('message: %s' % message)
                school = a_sheet.student.school
                mobile = a_sheet.student.parent.parent_mobile1
                sms.send_sms1(school, 'admin@jps.com', mobile, message, 'Share Answer sheet')
                a_sheet.shared = True
                a_sheet.save()
        return JSONResponse({}, status=200)
