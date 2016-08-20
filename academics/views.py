from django.shortcuts import render

# Create your views here.

import json
import datetime
from datetime import date

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.test import RequestFactory

from authentication.views import JSONResponse

from rest_framework import generics
from threading import Thread
import Queue

from attendance.models import Attendance, AttendanceTaken
from teacher.models import Teacher
from student.models import Student
from setup.models import Configurations, School
from .models import Class, Section, Subject, ClassTest, TestResults, WorkingDays, Exam
from .serializers import ClassSerializer, SectionSerializer, \
    SubjectSerializer, TestSerializer, ClassSectionForTestSerializer, \
    TestMarksSerializer, TestTypeSerializer, ExamSerializer

from operations import sms


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
        the_class = student.current_class
        class_sequence = the_class.sequence
        q = Exam.objects.filter(start_class_sequence__lte=class_sequence, end_class_sequence__gte=class_sequence)
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
        return q


class PendingTestList(generics.ListCreateAPIView):
    serializer_class = TestSerializer

    def get_queryset(self):
        t = self.kwargs['teacher']

        the_teacher = Teacher.objects.get(email=t)

        q = ClassTest.objects.filter(teacher=the_teacher, is_completed=False).order_by('date_conducted')
        return q


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


# we need to exempt this view from csrf verification. Will be updated in next version when
# we will implement authentication
@csrf_exempt
def create_test(request, the_class, section, subject, teacher, d, m, y, max_marks, pass_marks, grade_based, comments):
    if request.method == 'POST':
        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        c = Class.objects.get(standard=the_class)
        print c
        s = Section.objects.get(section=section)
        print s
        sub = Subject.objects.get(subject_name=subject)
        print sub
        t = Teacher.objects.get(email=teacher)
        print t
        the_date = date(int(y), int(m), int(d))
        print the_date

        # check to see if this test has already been created.
        try:
            q = ClassTest.objects.filter(date_conducted=the_date, the_class=c, section=s, subject=sub, teacher=t)
            print q.count()

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
                    print 'grade_based is 0'
                    test.grade_based = True

                if grade_based == '1':
                    print 'grade_based is 1'
                    test.grade_based = False

                print grade_based

                test.test_type = comments
                test.is_completed = False

                try:
                    test.save()
                    print 'test successfully created'

                except Exception as e:
                    print 'Test creation failed'
                    print 'Exception = %s (%s)' % (e.message, type(e))
                    return HttpResponse('Test Creation Failed')

                # now, create entry for each student in table TestResults. We need to retrieve the list of student
                # of the class associated with this test
                student_list = Student.objects.filter(current_section__section=section,
                                                      current_class__standard=the_class, active_status=True)
                for student in student_list:
                    # -5000.00 marks indicate null value
                    test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                              student=student, marks_obtained=-5000.00, grade='')
                    try:
                        test_result.save()
                        print ' test results successfully created'
                    except Exception as e:
                        print 'failed to create test results'
                        print 'Exception = %s (%s)' % (e.message, type(e))
                        return HttpResponse('Failed to create test results')
            else:
                print 'Test already exist'
                return HttpResponse('Test already exist')
        except Exception as e:
            print 'Exception = %s (%s)' % (e.message, type(e))
            return HttpResponse('Failed')

    # this view is being called from mobile. We use dummy template so that we dont' run into exception
    # return render(request, 'classup/dummy.html')
    return HttpResponse('OK')


# we need to exempt this view from csrf verification. Will be updated in next version when
# we will implement authentication


@csrf_exempt
def save_marks(request):
    if request.method == 'POST':
        response = {

        }
        print 'request.body='
        print request.body
        # convert the raw data received to json
        data = json.loads(request.body)
        print 'json='
        print data

        # determine whether this test is marks based or grade based
        grade_based = False
        for key in data:
            test = ClassTest.objects.get(testresults__id=key)
            break  # because we can get the test object with the first key only

        if test.grade_based:
            grade_based = True
            print 'this is a grade based test'

        # iterate over json and save/update marks
        for key in data:
            tr = TestResults.objects.get(pk=key)

            if grade_based:
                print 'saving grade....'
                tr.grade = data[key]
            else:
                tr.marks_obtained = float(data[key])

            try:
                tr.save()
            except Exception as e:
                print('unable to save marks')
                print 'Exception = %s (%s)' % (e.message, type(e))

        response["status"] = "success"

        return JSONResponse(response, status=200)


@csrf_exempt
def submit_marks(request):
    t1 = datetime.datetime.now()
    message_list = {

    }
    if request.method == 'POST':
        response = {

        }
        # convert the raw data received to json
        data = json.loads(request.body)

        configuration = Configurations.objects.get(pk=1)
        school_name = configuration.school_name

        # determine whether this test is marks based or grade based
        grade_based = False
        for key in data:
            test = ClassTest.objects.get(testresults__id=key)
            break  # because we can get the test object with the first key only

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
                tr.marks_obtained = float(data[key])
                if float(data[key]) > highest_marks:
                    highest_marks = float(data[key])
                    if highest_marks.is_integer():
                        highest_marks = int(highest_marks)
                if float(data[key]) != float(-1000):
                    mark_total += float(data[key])
                    present_count += 1
                    average_marks = float(mark_total / present_count)
                    if average_marks.is_integer():
                        average_marks = int(average_marks)
            try:
                tr.save()
            except Exception as e:
                print('unable to save marks')
                print 'Exception = %s (%s)' % (e.message, type(e))

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
            print 'initial=' + str(initial)
            if initial > threshold:
                print 'exiting due to threshold was hit'
                response["status"] = "success"
                return JSONResponse(response, status=200)

            # print data[key]
            tr = TestResults.objects.get(pk=key)
            student = tr.student
            print student

            try:

                sub = test.subject

                message = 'Dear Ms/Mr ' + student.parent.parent_name + ', your ward ' + student.fist_name + \
                          ' ' + student.last_name + ' '

                if grade_based:
                    if data[key] == '-1000.00' or data[key] == '-1000':
                        message += 'was ABSENT in the test of '
                    else:
                        message += 'has secured ' + tr.grade + ' grade in the test of '
                else:
                    if data[key] == '-1000.00' or data[key] == '-1000':
                        message += 'was ABSENT in the test of '
                    else:
                        marks = float(tr.marks_obtained)
                        if marks.is_integer():
                            marks = int(marks)
                        message += 'has secured ' + str(marks) + ' marks out of ' + str(int(test.max_marks))
                        message += ' in the test of '

                message += sub.subject_name + ' held on ' + dmy_date

                if not grade_based:
                    message += '. Highest marks secured in this test are ' + str(highest_marks)
                    message += ' & Average marks secured in this test are ' + str(round(average_marks))
                message += ". Regards, " + school_name

                # print message

                p = student.parent
                # print p
                m1 = p.parent_mobile1
                message_list[m1] = message
                m2 = p.parent_mobile2
                # print "mobile1=" + m1
                # print "mobile2=" + m2

                # 11/20 - we may need to send sms for about 40-50 students, which can be time consumeing.
                # Hence we use thread

                # 11/21 afrer several trial runs it is observed that on server where we use uwsgi, implemenation
                # threading results in sending same sms several times thsus increasing costs. This may be due to the
                # face that uwsgi spawns its own thread and then our thread gets mixed with uwsgin thread. Hence, turn
                # off threading till some solution is found

                result = Queue.Queue()

                # thread1 = Thread(target=sms.send_sms, args=(m1, message, result))
                # thread1 = Thread(target=sms.send_sms, args=(m1, message))
                # thread1.start()
                # thread1.join()
                # sms.send_sms(m1, message)

                if m2 != '':
                    message_list[m2] = message
                    # pass
                    # thread2 = Thread(target=sms.send_sms, args=(m2, message, result))
                    # thread2 = Thread(target=sms.send_sms, args=(m2, message))
                    # thread2.start()
                    # thread2.join()
                    # sms.send_sms(m2, message)

            except Exception as e1:
                print 'unable send sms for ' + student.fist_name + ' ' + student.last_name
                print 'Exception = %s (%s)' % (e1.message, type(e1))

                # p = student.parent
                # print p
                # m1 = p.parent_mobile1
                # m2 = p.parent_mobile2
                # print "mobile1=" + m1
                # print "mobile2=" + m2
                #
                # sms.send_sms(m1, message)
                #
                # if m2 != '':
                #     sms.send_sms(m2, message)
        t = Thread(target=sms.send_sms_asynch(message_list))
        t.start()
        count = 0
        for mobile in message_list:
            print mobile
            print message_list[mobile]
            count += 1
            print count
        t2 = datetime.datetime.now()
        print 'execution took ' + str(t2 - t1)
        response["status"] = "success"
        return JSONResponse(response, status=200)


@csrf_exempt
def get_working_days(request):
    print 'I am being executed the old get_working_days'
    print 'request for calculating working days started at='
    print datetime.datetime.now()
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
    c = Configurations.objects.get(pk=1)
    session_start_month = c.session_start_month

    if request.method == 'GET':

        y = request.GET.get('year')
        m = request.GET.get('month')
        print 'while caculating workig days, year from request=' + y

        if y != 'till_date':
            try:
                total_days = WorkingDays.objects.get(year=y, month=month_dict[m])
                print 'days in ' + str(month_dict[m]) + '/' + str(y) + '=' + str(total_days.working_days)
                response['working_days'] = total_days.working_days
                return JSONResponse(response, status=200)
            except Exception as e:
                print 'unable to fetch the number of days for ' + str(m) + '/' + str(y)
                print 'Exception = %s (%s)' % (e.message, type(e))
                return JSONResponse('Failed', status=404)
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
                        total_days = WorkingDays.objects.get(year=now.year - 1, month=m)
                        print 'days in ' + str(m) + '/' + str(now.year - 1) + '=' + str(total_days.working_days)
                        days_till_last_month += total_days.working_days
                    except Exception as e:
                        print 'unable to fetch the number of days for ' + str(m) + '/' + str(now.year - 1)
                        print 'Exception = %s (%s)' % (e.message, type(e))
                        return JSONResponse('Failed', status=404)
                for m in range(1, now.month):
                    try:
                        total_days = WorkingDays.objects.get(year=now.year, month=m)
                        print 'days in ' + str(m) + '/' + str(now.year) + '=' + str(total_days.working_days)
                        days_till_last_month += total_days.working_days
                    except Exception as e:
                        print 'unable to fetch the number of days for ' + str(m) + '/' + str(now.year)
                        print 'Exception = %s (%s)' % (e.message, type(e))
                        return JSONResponse('Failed', status=404)
            # if current month is higher than the session_start_month then we need to add the working days
            # session start month till current-1 month
            else:
                for m in range(session_start_month, now.month):
                    try:
                        total_days = WorkingDays.objects.get(year=now.year, month=m)
                        print 'days in ' + str(m) + '/' + str(now.year) + '=' + str(total_days.working_days)
                        days_till_last_month += total_days.working_days
                    except Exception as e:
                        print 'unable to fetch the number of days for ' + str(m) + '/' + str(now.year)
                        print 'Exception = %s (%s)' % (e.message, type(e))
                        return JSONResponse('Failed', status=404)
            response['working_days'] = days_till_last_month
            return JSONResponse(response, status=200)
    print 'request for calculating working days finished at='
    print datetime.datetime.now()
    return HttpResponse('OK')


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
    c = Configurations.objects.get(pk=1)
    session_start_month = c.session_start_month

    if request.method == 'GET':

        y = request.GET.get('year')
        print y
        mo = request.GET.get('month')
        m = month_dict[mo]
        cl = request.GET.get('class')
        the_section = request.GET.get('section')
        the_subject = request.GET.get('subject')

        the_class = Class.objects.get(standard=cl)
        section = Section.objects.get(section=the_section)

        # 11/08/2016 earlier the summary was based on the main only but now they can be for any specific subject
        # main = Subject.objects.get(subject_name='Main')
        subject = Subject.objects.get(subject_name=the_subject)

        if y != 'till_date':
            print 'calculating working days for the month ' + mo + ' of year ' + y
            try:
                query = AttendanceTaken.objects.filter(date__month=m, date__year=y, subject=subject,
                                                       the_class=the_class, section=section)
                total_days = query.count()
                print 'total days found = ' + str(total_days)

                response['working_days'] = total_days
                return JSONResponse(response, status=200)
            except Exception as e:
                print 'unable to fetch the number of days for ' + str(m) + '/' + str(y)
                print 'Exception = %s (%s)' % (e.message, type(e))
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
                        query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year - 1, subject=subject,
                                                               the_class=the_class, section=section)
                        total_days = query.count()
                        print 'days in ' + str(m) + '/' + str(now.year - 1) + '=' + str(total_days)
                        days_till_last_month += total_days
                    except Exception as e:
                        print 'unable to fetch the number of days for ' + str(m) + '/' + str(now.year - 1)
                        print 'Exception = %s (%s)' % (e.message, type(e))
                        return JSONResponse('Failed', status=404)
                for m in range(1, now.month + 1):
                    try:
                        query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year, subject=subject,
                                                               the_class=the_class, section=section)
                        total_days = query.count()
                        print 'days in ' + str(m) + '/' + str(now.year - 1) + '=' + str(total_days)
                        days_till_last_month += total_days
                    except Exception as e:
                        print 'unable to fetch the number of days for ' + str(m) + '/' + str(now.year)
                        print 'Exception = %s (%s)' % (e.message, type(e))
                        return JSONResponse('Failed', status=404)
            # if current month is higher than the session_start_month then we need to add the working days
            # session start month till current-1 month
            else:
                for m in range(session_start_month, now.month + 1):
                    try:
                        query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year, subject=subject,
                                                               the_class=the_class, section=section)
                        total_days = query.count()
                        print 'days in ' + str(m) + '/' + str(now.year - 1) + '=' + str(total_days)
                        days_till_last_month += total_days
                    except Exception as e:
                        print 'unable to fetch the number of days for ' + str(m) + '/' + str(now.year)
                        print 'Exception = %s (%s)' % (e.message, type(e))
                        return JSONResponse('Failed', status=404)
            response['working_days'] = days_till_last_month
            return JSONResponse(response, status=200)
    print datetime.datetime.now()
    return HttpResponse('OK')


def get_attendance_summary(request):
    print 'request for attendance summary started at='
    print datetime.datetime.now()
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
    c = Configurations.objects.get(pk=1)
    session_start_month = c.session_start_month
    dict_attendance_summary = {

    }

    response_array = []

    if request.method == 'GET':
        c = request.GET.get('class')
        sec = request.GET.get('section')
        sub = request.GET.get('subject')
        m = request.GET.get('month')
        y = request.GET.get('year')
        print 'while in attendance summary, year from request=' + y

        # get the number of working days for the duration mentioned in request (for a specific month or till date)
        # we are re-using the view get_working_days. We need to simulate an HTTP GET request to use the view
        factory = RequestFactory()

        request = factory.get('/academics/get_working_days1/?year=' + y +
                              '&month=' + m + '&class=' + c + '&section=' + sec + '&subject=' + sub)

        # the response contains newlines and Content type information. Hence it cannot be converted to json as it is.
        # we need to remove newlines and content type in order to convert it to json
        response = str(get_working_days1(request))
        data = response.replace('Content-Type: application/json', '')

        data = data.strip('\r\n')
        json_data = json.loads(data)
        working_days = json_data['working_days']
        print working_days

        print 'working days=' + str(json_data['working_days'])

        # get the list of students for the given class, section,
        q = Student.objects.filter(current_section__section=sec, current_class__standard=c, active_status=True)
        subject = Subject.objects.get(subject_name=sub)
        # for this subject and duration get the number of absent days for each student one by one. Also, keep
        # on building the json to be returned
        for s in q:
            if y != 'till_date':
                try:
                    query = Attendance.objects.filter \
                        (student=s, subject=subject, date__month=month_dict[m], date__year=y)
                    absent_days = query.count()
                except Exception as e:
                    print 'Exception = %s (%s)' % (e.message, type(e))
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
                            print 'absent days for ' + str(m) + '/' + str(now.year - 1) + '=' + str(query.count())
                        except Exception as e:
                            print 'unable to fetch absent days for ' + str(m) + '/' + str(now.year - 1)
                            print 'Exception = %s (%s)' % (e.message, type(e))
                            return JSONResponse('Failed', status=404)
                    for m in range(1, now.month):
                        try:
                            query = Attendance.objects.filter \
                                (student=s, subject=subject, date__month=m, date__year=now.year)
                            absent_days += query.count()
                            print 'absent days for ' + str(m) + '/' + str(now.year) + '=' + str(query.count())
                        except Exception as e:
                            print 'unable to fetch absent days for ' + str(m) + '/' + str(now.year)
                            print 'Exception = %s (%s)' % (e.message, type(e))
                            return JSONResponse('Failed', status=404)
                # if current month is higher than the session_start_month then we need to add the working days
                # session start month till current-1 month
                else:
                    for m in range(session_start_month, now.month):
                        try:
                            query = Attendance.objects.filter \
                                (student=s, subject=subject, date__month=m, date__year=now.year)
                            absent_days += query.count()

                            print 'absent days for ' + str(m) + '/' + str(now.year) + '=' + str(query.count())
                        except Exception as e:
                            print 'unable to fetch absent days for ' + str(m) + '/' + str(now.year)
                            print 'Exception = %s (%s)' % (e.message, type(e))
                            return JSONResponse('Failed', status=404)
            # response['working_days'] = days_till_last_month
            print 'absent days=' + str(absent_days)
            present_days = working_days - absent_days
            # calculate the % of present days
            if int(working_days) < 1:
                dict_attendance_summary['percentage'] = 'N/A'
            else:
                present_perc = round((float(present_days) / float(working_days)) * 100, 2)
                dict_attendance_summary['percentage'] = str(present_perc) + '%'

            print 'present days=' + str(present_days)

            dict_attendance_summary['name'] = s.fist_name + ' ' + s.last_name
            dict_attendance_summary['roll_number'] = s.roll_number

            dict_attendance_summary['present_days'] = str(present_days)
            d = dict(dict_attendance_summary)
            response_array.append(d)

        print response_array.__len__()

        print 'request for attendance summary finished at='
        print datetime.datetime.now()
        return JSONResponse(response_array, status=200)


@csrf_exempt
def delete_test(request, test_id):
    response = {

    }
    if request.method == 'DELETE':
        try:
            t = ClassTest.objects.get(pk=int(test_id))
            t.delete()
            response["status"] = "success"
            return JSONResponse(response, status=200)
        except Exception as e:
            response["status"] = "failed"
            print('Unable to delete test with id=' + test_id)
            print 'Exception = %s (%s)' % (e.message, type(e))
            return JSONResponse(response, status=404)



