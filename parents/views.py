import datetime
import calendar
import json

from rest_framework import generics
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from authentication.views import JSONResponse
from student.models import Student
from setup.models import Configurations
from academics.models import Subject, Class, Section, ClassTeacher, ClassTest, TestResults, Exam
from attendance.models import AttendanceTaken, Attendance

from operations import sms

from .models import ParentCommunicationCategories, ParentCommunication

from .serializers import ParentsCommunicationCategorySerializer

# Create your views here.


class CategoryList(generics.ListCreateAPIView):
    queryset = ParentCommunicationCategories.objects.all().order_by('category')
    serializer_class = ParentsCommunicationCategorySerializer


@csrf_exempt
def submit_parents_communication(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        student_id = data['student_id']
        cat = data['category']
        communication_text = data['communication_text']

        student = Student.objects.get(id=student_id)
        configuration = Configurations.objects.get(school=student.school)

        # student and category are foreign keys

        category = ParentCommunicationCategories.objects.get(category=cat)

        # now, create the ParentCommunicationObject
        try:
            pc = ParentCommunication(student=student, category=category, date_sent=datetime.datetime.now(),
                                     communication_text=communication_text)
            pc.save()
            print ('successfully saved the message "' + communication_text + '" in the database')
            # if the message was for Class Teacher/Principal's immediate attention an sms need to be sent to them
            if cat == 'Class Teacher/Principal Attention' or cat == 'Leave Application' \
                    or configuration.send_all_parent_sms_to_principal:
                try:
                    parent = student.parent
                    parent_name = parent.parent_name
                    parent_mobile = parent.parent_mobile1
                    the_class = student.current_class
                    section = student.current_section

                    # compose the message
                    message = communication_text + '. Regards, ' + parent_name + ' (' + parent_mobile + ')'
                    message += ', Parent of '
                    message += student.fist_name + ' ' + student.last_name + ' (class '
                    message += the_class.standard + '-' + section.section + ')'
                    print (message)

                    # sometimes class teacher may not be set
                    try:
                        ct = ClassTeacher.objects.get(standard=the_class, section=section)
                        if ct:
                            teacher = ct.class_teacher
                            teacher_mobile = teacher.mobile
                            sms.send_sms(teacher_mobile, message)
                    except Exception as e:
                        print('Class Teacher not set for ' + the_class.standard + '-' + section.section)
                        print ('Exception = %s (%s)' % (e.message, type(e)))

                    principal_mobile = configuration.principal_mobile
                    sms.send_sms(principal_mobile, message)
                except Exception as e:
                    print ('failed to send message ' + communication_text + ' to Class Teacher of class ' +
                           the_class.standard + '-' + section.section)
                    print ('Exception = %s (%s)' % (e.message, type(e)))

            return HttpResponse('Success')
        except Exception as e:
            print ('Error occured while trying to save comments from parents of '
                   + student.fist_name + ' ' + student.last_name)
            print ('Exception = %s (%s)' % (e.message, type(e)))
            return HttpResponse('Failed')

    return HttpResponse('OK')


def retrieve_stu_att_summary(request):

    dict_attendance_summary = {

    }
    response_array = []

    if request.method == 'GET':
        student_id = request.GET.get('student_id')
    student = Student.objects.get(id=student_id)
    school = student.school
    c = Configurations.objects.get(school=school)
    session_start_month = c.session_start_month
    print (session_start_month)

    the_class = student.current_class
    section = student.current_section

    # 22/08/2016 logic - Coaching classes and Colleges prefer to condcuct attendance subject wise and hence
    # Main subject may not exist for them. In this case we will be presenting the aggregate of attendance for all
    # the subjects. This will be done by first checking the existence of subject Main. If it is present the
    # calculations are based on attendance in Main subjects, else aggregate of all subjects
    main_exist = True
    try:
        main = Subject.objects.get(school=school, subject_name='Main')
    except Exception as e:
        print ('Main subject does not exist for this school/Coaching Institute')
        print ('Exception = %s (%s)' % (e.message, type(e)))
        main_exist = False

    now = datetime.datetime.now()
    work_days = 0
    if now.month < session_start_month:
        print ('current month is less than session start month. Hence starting from last year')
        for m in range(session_start_month, 12 + 1):  # 12+1, because loop executes for 1 time less than max index
            month_year = calendar.month_abbr[m] + '/' + str(now.year-1)
            dict_attendance_summary["month_year"] = month_year
            try:
                if main_exist:
                    query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year - 1, subject=main,
                                                           the_class=the_class, section=section)
                else:
                    query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year - 1,
                                                           the_class=the_class, section=section)
                work_days = query.count()
                dict_attendance_summary["work_days"] = work_days
                print ('days in ' + str(m) + '/' + str(now.year - 1) + '=' + str(work_days))
            except Exception as e:
                print ('unable to fetch the number of days for ' + month_year)
                print ('Exception = %s (%s)' % (e.message, type(e)))
            try:
                if main_exist:
                    query = Attendance.objects.filter(student=student, subject=main,
                                                      date__month=m, date__year=now.year - 1)
                else:
                    query = Attendance.objects.filter(student=student, date__month=m, date__year=now.year - 1)
                absent_days = query.count()
                dict_attendance_summary["absent_days"] = absent_days
                present_days = work_days - absent_days
                dict_attendance_summary["present_days"] = present_days

                if work_days != 0:
                    present_perc = round((float(present_days)/float(work_days))*100, 2)
                    dict_attendance_summary['percentage'] = str(present_perc) + '%'
                else:
                    dict_attendance_summary['percentage'] = 'N/A'
                print ('absent days for ' + str(m) + '/' + str(now.year - 1) + '=' + str(query.count()))
            except Exception as e:
                print ('unable to fetch absent days for ' + str(m) + '/' + str(now.year - 1))
                print ('Exception = %s (%s)' % (e.message, type(e)))
            d = dict(dict_attendance_summary)
            response_array.append(d)
        for m in range(1, now.month+1):
            month_year = calendar.month_abbr[m] + '/' + str(now.year)
            dict_attendance_summary["month_year"] = month_year
            try:
                if main_exist:
                    query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year,
                                                           subject=main,the_class=the_class, section=section)
                else:
                    query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year,
                                                           the_class=the_class, section=section)
                work_days = query.count()
                dict_attendance_summary["work_days"] = work_days
                print ('days in ' + str(m) + '/' + str(now.year) + '=' + str(work_days))
            except Exception as e:
                print ('unable to fetch the number of days for ' + str(m) + '/' + str(now.year))
                print ('Exception = %s (%s)' % (e.message, type(e)))
            try:
                if main_exist:
                    query = Attendance.objects.filter(student=student, subject=main,
                                                      date__month=m, date__year=now.year)
                else:
                    query = Attendance.objects.filter(student=student, date__month=m, date__year=now.year)
                absent_days = query.count()
                dict_attendance_summary["absent_days"] = absent_days
                present_days = work_days - absent_days
                dict_attendance_summary["present_days"] = present_days
                if work_days != 0:
                    present_perc = round((float(present_days)/float(work_days))*100, 2)
                    dict_attendance_summary['percentage'] = str(present_perc) + '%'
                else:
                    dict_attendance_summary['percentage'] = 'N/A'
                print ('absent days for ' + str(m) + '/' + str(now.year) + '=' + str(query.count()))
            except Exception as e:
                print ('unable to fetch absent days for ' + str(m) + '/' + str(now.year))
                print ('Exception = %s (%s)' % (e.message, type(e)))
            d = dict(dict_attendance_summary)
            response_array.append(d)

    # if current month is higher than the session_start_month then we need to add the working days
    # session start month till current-1 month
    else:
        for m in range(session_start_month, now.month+1):
            month_year = calendar.month_abbr[m] + '/' + str(now.year)
            dict_attendance_summary["month_year"] = month_year
            try:
                if main_exist:
                    query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year,
                                                           subject=main, the_class=the_class, section=section)
                else:
                    query = AttendanceTaken.objects.filter(date__month=m, date__year=now.year,
                                                           the_class=the_class, section=section)
                work_days = query.count()
                dict_attendance_summary["work_days"] = work_days
                print ('days in ' + str(m) + '/' + str(now.year) + '=' + str(work_days))
            except Exception as e:
                print ('unable to fetch the number of days for ' + str(m) + '/' + str(now.year))
                print ('Exception = %s (%s)' % (e.message, type(e)))
            try:
                if main_exist:
                    query = Attendance.objects.filter (student=student, subject=main,
                                                       date__month=m, date__year=now.year)
                else:
                    query = Attendance.objects.filter(student=student, date__month=m, date__year=now.year)
                absent_days = query.count()
                dict_attendance_summary["absent_days"] = absent_days
                present_days = work_days - absent_days
                dict_attendance_summary["present_days"] = present_days
                if work_days != 0:
                    present_perc = round((float(present_days)/float(work_days))*100, 2)
                    dict_attendance_summary['percentage'] = str(present_perc) + '%'
                else:
                    dict_attendance_summary['percentage'] = 'N/A'

                print ('absent days for ' + str(m) + '/' + str(now.year) + '=' + str(query.count()))

            except Exception as e:
                print ('unable to fetch absent days for ' + str(m) + '/' + str(now.year))
                print ('Exception = %s (%s)' % (e.message, type(e)))
            d = dict(dict_attendance_summary)

            response_array.append(d)
    print (response_array.__len__())

    return JSONResponse(response_array, status=200)


def retrieve_student_subjects(request):
    subject_list = {

    }
    response_array = []

    if request.method == 'GET':
        student = request.GET.get('student')
        print (student)
        try:
            s = Student.objects.get(id=student)
            c = s.current_class
            sect = s.current_section

            test_list = ClassTest.objects.filter(the_class=c, section=sect, is_completed=True)
            for test in test_list:
                subject = test.subject.subject_name
                subject_list['subject'] = subject
                d = dict(subject_list)
                response_array.append(d)
            return JSONResponse(response_array, status=200)
        except Exception as e:
            print ('unable to retrieve list of sbujects for ' + s.fist_name + ' ' + s.last_name)
            print ('Exception = %s (%s)' % (e.message, type(e)))
    return JSONResponse(response_array, status=201)


def retrieve_stu_sub_marks_history(request, subject):
    marks_history = {

    }
    response_array = []

    if request.method == 'GET':
        student = request.GET.get('student')

        try:
            sub = Subject.objects.get(subject_name=subject)
            s = Student.objects.get(id=student)
            c = s.current_class
            sect = s.current_section

            test_list = ClassTest.objects.filter(the_class=c, section=sect, subject=sub, is_completed=True).\
                order_by('date_conducted')
            for test in test_list:
                marks_history['date'] = test.date_conducted

                test_result = TestResults.objects.get(class_test=test, student=s)
                if test.grade_based:
                    marks_history['max_marks'] = 'Grade Based'
                    marks_history['marks'] = test_result.grade
                else:
                    marks_history['max_marks'] = test.max_marks
                    marks_history['marks'] = test_result.marks_obtained
                d = dict(marks_history)
                response_array.append(d)
            return JSONResponse(response_array, status=200)
        except Exception as e:
            print ('Exception = %s (%s)' % (e.message, type(e)))
            print ('unable to retrieve ' + sub.subject_name + ' marks history for '
                   + s.fist_name + ' ' + s.last_name)

    return JSONResponse(response_array, status=201)


def get_exam_result(request, student_id, exam_id):
    exam_result = {

    }
    response_array = []

    if request.method == 'GET':
        student = Student.objects.get(id=student_id)
        print (student)
        exam = Exam.objects.get(id=exam_id)
        print (exam)

        start_date = exam.start_date
        end_date = exam.end_date

        # get the list of tests conducted for the class/section of the student between the exam start and end dates
        try:
            test_list = ClassTest.objects.filter(date_conducted__gte=start_date, date_conducted__lte=end_date,
                                                 the_class=student.current_class, section=student.current_section)
            print (test_list)
            for test in test_list:
                if test.is_completed:
                    print (test)
                    exam_result['subject'] = test.subject.subject_name
                    print (exam_result)

                    test_result = TestResults.objects.filter(class_test=test, student=student)
                    print (test_result)
                    if test.grade_based:
                        exam_result['max_marks'] = 'Grade Based'
                        for tr in test_result:
                            exam_result['marks'] = tr.grade
                            break
                    else:
                        exam_result['max_marks'] = test.max_marks
                        for tr in test_result:
                            print (tr.marks_obtained)
                            exam_result['marks'] = tr.marks_obtained
                            break

                    d = dict(exam_result)
                    response_array.append(d)
            return JSONResponse(response_array, status=200)
        except Exception as e:
            print (exam_result)
            print ('Exception = %s (%s)' % (e.message, type(e)))
            print ('unable to retrieve ' + exam.title + ' results for ' +
                   student.fist_name + ' ' + student.last_name)
    return JSONResponse(response_array, status=201)