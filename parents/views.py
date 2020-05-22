import datetime
import calendar
import json
import xlrd

from rest_framework import generics

from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max, Sum

from authentication.views import JSONResponse, log_entry
from student.models import Student
from setup.models import School, Configurations
from academics.models import Subject, ClassTeacher, ClassTest, TestResults, TermTestResult, Exam
from attendance.models import AttendanceTaken, Attendance
from setup.forms import ExcelFileUploadForm
from setup.views import validate_excel_extension

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
        school = student.school
        configuration = Configurations.objects.get(school=school)

        # student and category are foreign keys

        category = ParentCommunicationCategories.objects.get(category=cat)

        # now, create the ParentCommunicationObject
        try:
            pc = ParentCommunication(student=student, category=category, date_sent=datetime.datetime.now(),
                                     communication_text=communication_text)
            pc.save()
            print ('successfully saved the message "' + communication_text + '" in the database')

            try:
                parent_mobile = student.parent.parent_mobile1
                action = 'Submitted Parent Communication'
                log_entry(parent_mobile, action, 'Normal', True)
            except Exception as e:
                print('unable to create logbook entry')
                print ('Exception 500 from parents views.py %s %s' % (e.message, type(e)))

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
                    message_type = 'Parent Communication'
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
                            sms.send_sms1(school, parent_name, teacher_mobile, message, message_type)
                            try:
                                parent_mobile = student.parent.parent_mobile1
                                action = 'Parent Communication SMS sent to Class Teacher: '
                                action += teacher.first_name + ' ' + teacher.last_name
                                log_entry(parent_mobile, action, 'Normal', True)
                            except Exception as e:
                                print('unable to create logbook entry')
                                print ('Exception 501 from parents views.py %s %s' % (e.message, type(e)))
                    except Exception as e:
                        print('Class Teacher not set for ' + the_class.standard + '-' + section.section)
                        print ('Exception 1 from parents views.py = %s (%s)' % (e.message, type(e)))

                    # 23/07/2019 leave applications need not be sent to principal
                    if cat != 'Leave Application':
                        try:
                            principal_mobile = configuration.principal_mobile
                            sms.send_sms1(school, parent_name, principal_mobile, message, message_type)
                        except Exception as e:
                            print('unable to send Parent communication to Principal')
                            print ('Exception 502-A from parents views.py %s %s' % (e.message, type(e)))

                        # 21/09/2017 - added so that apart from Principal, some other responsible staff can also receive
                        # the message
                        try:
                            admin1_mobile = configuration.admin1_mobile
                            # sms.send_sms1(school, parent_name, admin1_mobile, message, message_type)
                        except Exception as e:
                            print('unable to send Parent communication to Admin 1')
                            print ('Exception 502-B from parents views.py %s %s' % (e.message, type(e)))
                        try:
                            parent_mobile = student.parent.parent_mobile1
                            action = 'Parent Communication SMS sent to Principal'
                            log_entry(parent_mobile, action, 'Normal', True)
                        except Exception as e:
                            print('unable to create logbook entry')
                            print ('Exception 502 from parents views.py %s %s' % (e.message, type(e)))
                except Exception as e:
                    print ('failed to send message ' + communication_text + ' to Class Teacher of class ' +
                           the_class.standard + '-' + section.section)
                    print ('Exception 2 from parents views.py = %s (%s)' % (e.message, type(e)))
            return HttpResponse('Success')
        except Exception as e:
            print ('Error occured while trying to save comments from parents of '
                   + student.fist_name + ' ' + student.last_name)
            print ('Exception 3 from parents views.py = %s (%s)' % (e.message, type(e)))
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

    # 22/08/2016 logic - Coaching classes and Colleges prefer to conduct attendance subject wise and hence
    # Main subject may not exist for them. In this case we will be presenting the aggregate of attendance for all
    # the subjects. This will be done by first checking the existence of subject Main. If it is present the
    # calculations are based on attendance in Main subjects, else aggregate of all subjects
    main_exist = True
    try:
        main = Subject.objects.get(school=school, subject_name='Main')
    except Exception as e:
        print ('Main subject does not exist for this school/Coaching Institute')
        print ('Exception4 from parents views.py = %s (%s)' % (e.message, type(e)))
        main_exist = False

    now = datetime.datetime.now()
    work_days = 0
    if now.month < session_start_month:
        print ('current month is less than session start month. Hence starting from last year')
        for m in range(session_start_month, 12 + 1):  # 12+1, because loop executes for 1 time less than max index
            month_year = calendar.month_abbr[m] + '/' + str(now.year - 1)
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
                print ('Exception5 from parents views.py = %s (%s)' % (e.message, type(e)))
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
                    present_perc = round((float(present_days) / float(work_days)) * 100, 2)
                    dict_attendance_summary['percentage'] = str(present_perc) + '%'
                else:
                    dict_attendance_summary['percentage'] = 'N/A'
                print ('absent days for ' + str(m) + '/' + str(now.year - 1) + '=' + str(query.count()))
            except Exception as e:
                print ('unable to fetch absent days for ' + str(m) + '/' + str(now.year - 1))
                print ('Exception6 from parents views.py = %s (%s)' % (e.message, type(e)))
            d = dict(dict_attendance_summary)
            response_array.append(d)
        for m in range(1, now.month + 1):
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
                print ('Exception7 from parents views.py = %s (%s)' % (e.message, type(e)))
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
                    present_perc = round((float(present_days) / float(work_days)) * 100, 2)
                    dict_attendance_summary['percentage'] = str(present_perc) + '%'
                else:
                    dict_attendance_summary['percentage'] = 'N/A'
                print ('absent days for ' + str(m) + '/' + str(now.year) + '=' + str(query.count()))
            except Exception as e:
                print ('unable to fetch absent days for ' + str(m) + '/' + str(now.year))
                print ('Exception8 from parents views.py = %s (%s)' % (e.message, type(e)))
            d = dict(dict_attendance_summary)
            response_array.append(d)

    # if current month is higher than the session_start_month then we need to add the working days
    # session start month till current-1 month
    else:
        for m in range(session_start_month, now.month + 1):
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
                print ('Exception9 from parents views.py = %s (%s)' % (e.message, type(e)))
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
                    present_perc = round((float(present_days) / float(work_days)) * 100, 2)
                    dict_attendance_summary['percentage'] = str(present_perc) + '%'
                else:
                    dict_attendance_summary['percentage'] = 'N/A'

                print ('absent days for ' + str(m) + '/' + str(now.year) + '=' + str(query.count()))

            except Exception as e:
                print ('unable to fetch absent days for ' + str(m) + '/' + str(now.year))
                print ('Exception10 from parents views.py = %s (%s)' % (e.message, type(e)))
            d = dict(dict_attendance_summary)

            response_array.append(d)
    print (response_array.__len__())

    try:
        parent_mobile = student.parent.parent_mobile1
        action = 'Retrieved ' + student.fist_name + ' ' + student.last_name + ' Attendance History'
        log_entry(parent_mobile, action, 'Normal', True)
    except Exception as e:
        print('unable to create logbook entry')
        print ('Exception 505 from parents views.py %s %s' % (e.message, type(e)))

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
            try:
                parent_mobile = s.parent.parent_mobile1
                action = 'Retrieved Subject List for ' + s.fist_name + ' ' + s.last_name
                log_entry(parent_mobile, action, 'Normal', True)
            except Exception as e:
                print('unable to create logbook entry')
                print ('Exception 506 from parents views.py %s %s' % (e.message, type(e)))

            return JSONResponse(response_array, status=200)
        except Exception as e:
            print ('unable to retrieve list of subjects for ' + s.fist_name + ' ' + s.last_name)
            print ('Exception11 from parents views.py = %s (%s)' % (e.message, type(e)))
    return JSONResponse(response_array, status=201)


def retrieve_stu_sub_marks_history(request, subject):
    marks_history = {

    }
    response_array = []

    if request.method == 'GET':
        student = request.GET.get('student')

        try:

            s = Student.objects.get(id=student)
            sub = Subject.objects.get(school=s.school, subject_name=subject)
            c = s.current_class
            sect = s.current_section

            test_list = ClassTest.objects.filter(the_class=c, section=sect, subject=sub, is_completed=True). \
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
            try:
                parent_mobile = s.parent.parent_mobile1
                action = 'Retrieved ' + sub.subject_name + ' marks history for ' + s.fist_name + ' ' + s.last_name
                log_entry(parent_mobile, action, 'Normal', True)
            except Exception as e:
                print('unable to create logbook entry')
                print ('Exception 507 from parents views.py %s %s' % (e.message, type(e)))

            return JSONResponse(response_array, status=200)
        except Exception as e:
            print ('Exception 12 from parents views.py = %s (%s)' % (e.message, type(e)))
            print ('unable to retrieve ' + sub.subject_name + ' marks history for '
                   + s.fist_name + ' ' + s.last_name)

    return JSONResponse(response_array, status=201)


def get_exam_result(request, student_id, exam_id):
    exam_result = {

    }
    response_array = []

    higher_classes = ['XI', 'XII']
    ninth_tenth = ['IX', 'X']
    middle_classes = ['V', 'VI', 'VII', 'VIII']

    prac_subjects = ["Biology", "Physics", "Chemistry",
                     "Accountancy", "Business Studies", "Economics", "Fine Arts",
                     "Information Practices", "Informatics Practices", "Computer Science", "Painting",
                     "Physical Education"]

    if request.method == 'GET':
        student = Student.objects.get(id=student_id)
        student_name = '%s %s' % (student.fist_name, student.last_name)
        print (student_name)
        the_class = student.current_class.standard
        print('%s is in class %s' % (student_name, the_class))
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
                print (test)
                exam_result['subject'] = test.subject.subject_name
                print (exam_result)

                # 27/03/2018 - in case of third language in V-VIII, second language in IX and all subjects in XI
                # the student may have not opted for it. So a check has to be made
                try:
                    tr = TestResults.objects.get(class_test=test, student=student)
                    print (tr)
                    if test.grade_based:
                        exam_result['max_marks'] = 'Grade Based'
                        exam_result['marks'] = tr.grade
                        exam_result['average'] = 'N/A'
                        exam_result['highest'] = 'N/A'
                    else:
                        if test.test_type == 'term':
                            print('this is a term test')
                            exam_result['max_marks'] = 100
                            main = tr.marks_obtained
                            # if student was absent then main marks would be -1000
                            if float(main) < 0.0:
                                print('%s was absent in the test of %s' % (student_name, test.subject.subject_name))
                                main = 0.0
                            print('this is a term test. PA, Notebook Sub & Sub Enrich marks/prac will be considered')
                            ttr = TermTestResult.objects.get(test_result=tr)
                            if the_class in higher_classes:
                                prac = 0.0
                                if test.subject.subject_name in prac_subjects:
                                    prac = ttr.prac_marks
                                total = float(main) + float(prac)
                                exam_result['marks'] = total
                            else:
                                pa = ttr.periodic_test_marks
                                notebook = ttr.note_book_marks
                                sub_enrich = ttr.sub_enrich_marks
                                multi_asses = ttr.multi_asses_marks
                                total = float(main) + float(pa) + float(notebook) + float(sub_enrich) + float(
                                    multi_asses)
                                exam_result['marks'] = round(total, 2)
                        else:
                            print('this is a unit test')
                            exam_result['max_marks'] = test.max_marks
                            marks_obtained = tr.marks_obtained
                            print (marks_obtained)
                            if marks_obtained == -5000.00:
                                marks_obtained = ' '
                            exam_result['marks'] = marks_obtained
                            highest = TestResults.objects.filter(class_test=test).aggregate(Max('marks_obtained'))
                            exam_result['highest'] = highest['marks_obtained__max']

                            total = TestResults.objects.filter(class_test=test,
                                                               marks_obtained__gt=0).aggregate(Sum('marks_obtained'))
                            appeared = TestResults.objects.filter(class_test=test, marks_obtained__gt=0).count()
                            exam_result['appeared'] = appeared
                            exam_result['average'] = '%.2f' % float(total/appeared)

                    d = dict(exam_result)
                    response_array.append(d)
                except Exception as e:
                    print('exception 27032018-A from parents views.py %s %s' % (e.message, type(e)))
                    print('subject %s is not opted by %s' % (test.subject.subject_name, student_name))
            return JSONResponse(response_array, status=200)
        except Exception as e:
            print (exam_result)
            print ('Exception 13 from parents views.py = %s (%s)' % (e.message, type(e)))
            print ('unable to retrieve ' + exam.title + ' results for ' +
                   student.fist_name + ' ' + student.last_name)
    return JSONResponse(response_array, status=201)


def send_health_record(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    context_dict['school_name'] = request.session['school_name']

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Health Data'
    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                # determine the school for which this processing is done
                school_id = request.session['school_id']
                school = School.objects.get(id=school_id)
                sender = request.session['user']
                print('school=' + school.school_name)
                print ('now starting to process the uploaded file for sending Health data...')
                fileToProcess_handle = request.FILES['excelFile']

                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(fileToProcess_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
                sheet = fileToProcess.sheet_by_index(0)
                if sheet:
                    print('Successfully got hold of sheet!')

                for row in range(sheet.nrows):
                    # skip the header rows
                    if row == 0:
                        continue

                    print('Processing a new row')
                    erp_id = sheet.cell(row, 1).value
                    try:
                        student = Student.objects.get(school=school, student_erp_id=erp_id)
                        print ('dealing with % s %s' % (student.fist_name, student.last_name))
                        parent_name = student.parent.parent_name
                        mobile = student.parent.parent_mobile1

                        weight = sheet.cell(row, 3).value
                        if weight == '':
                            weight = 'N/A'
                        message = 'Dear %s, weight of your ward %s during last health checkup is %s KG' % \
                                  (parent_name, student.fist_name, weight)
                        message_type = 'Health Data Communication (Web)'
                        print(message)
                        sms.send_sms1(school, sender, mobile, message, message_type)
                    except Exception as e:
                        print ('failed to send health data for %s' % erp_id)
                        print ('Exception 041117-A from parents views.py %s %s ' % (e.message, type(e)))
                messages.success(request, 'health data sent to parents')
            except Exception as e:
                print ('invalid excel file uploaded. Please fix and upload again')
                print ('Exception 041117-B from parents views.py %s %s ' % (e.message, type(e)))
    else:
        # we are arriving at this page for the first time, hence show an empty form
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)
