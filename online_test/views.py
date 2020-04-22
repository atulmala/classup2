import datetime as dt
import json
from datetime import date as today

import xlrd

# Create your views here.
from rest_framework import generics
from rest_framework.authentication import BasicAuthentication

from academics.models import Class, Subject
from authentication.views import CsrfExemptSessionAuthentication, JSONResponse
from online_test.models import OnlineTest, OnlineQuestion, StudentTestAttempt, StudentQuestion
from setup.models import School
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
            fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
            sheet = fileToProcess.sheet_by_index(0)
            if sheet:
                print ('Successfully got hold of sheet!')
            row = 0
            for row1 in range(sheet.nrows):
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

                    col += 5
                    teacher_id = sheet.cell(row, col).value
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

                    # create online test
                    online_test = OnlineTest(school=school, the_class=the_class,
                                             subject=subject, teacher=teacher, date=test_date)
                    online_test.save()
                    row += 1
                if row > 1:
                    print('C - row = %i' % row)
                    col = 1
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
