import json
import xlrd
import StringIO
import xlsxwriter
import time
import datetime
import calendar

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation import ugettext

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics

from authentication.views import JSONResponse
from setup.forms import ExcelFileUploadForm
from exam.forms import ResultSheetForm
from setup.views import validate_excel_extension
from student.models import Student

from teacher.models import TeacherAttendance

from operations import sms

from .serializers import *
from .models import *


# Create your views here.


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class ArrangementListForTeachers(generics.ListAPIView):
    serializer_class = ArrangementSerializer

    def get_queryset(self):
        email = self.kwargs['teacher']
        teacher = Teacher.objects.get(email=email)
        q = Arrangements.objects.filter(teacher=teacher, date=datetime.datetime.today()).order_by('period')
        return q


class Periods(generics.ListAPIView):
    serializer_class = PeriodSerializer

    def get_queryset(self):
        print('inside get_queryset')
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        q = Period.objects.filter(school=school)
        return q


class PeriodList(generics.ListAPIView):
    serializer_class = CTimeTableSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        print('school_id = %s' % school_id)
        d = self.kwargs['day']
        print('d = %s' % d)
        f = self.kwargs['for']
        print('f = %s' % f)
        id = self.kwargs['id']
        print('id = %s' % id)

        if school_id != 'na':
            school = School.objects.get(id=school_id)

        day = DaysOfWeek.objects.get(day=d)

        if f == 'teacher':
            teacher = Teacher.objects.get(school=school, email=id)
            q = TimeTable.objects.filter(teacher=teacher, day=day).order_by('period__period')
            return q
        if f == 'student':
            student = Student.objects.get(pk=id)
            the_class = student.current_class
            section = student.current_section
            q = CTimeTable.objects.filter(the_class=the_class, section=section, day=day).order_by('period__period')
            return q


class SetPeriod(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        print(data)
        school_id = data['school_id']
        school = School.objects.get(id=school_id)

        d = data['day']
        day = DaysOfWeek.objects.get(day=d)

        standard = data['the_class']
        the_class = Class.objects.get(school=school, standard=standard)
        sec = data['section']
        section = Section.objects.get(school=school, section=sec)

        symbol = data['period']
        period = Period.objects.get(school=school, symbol=symbol)

        sub = data['subject']
        subject = Subject.objects.get(school=school, subject_name=sub)

        teacher_id = data['teacher_id']
        teacher = Teacher.objects.get(pk=teacher_id)

        # set the TimeTable table
        print('setting up inside the main time table')
        try:
            tt = TimeTable.objects.get(school=school, day=day, the_class=the_class, section=section, period=period)
            print('%s class %s-%s period # %s is already. '
                  'This will be updated' % (day, the_class, section, period))
            tt.subject = subject
            tt.teacher = teacher
            tt.save()
            message = '%s class %s-%s period # %s is now updated to %s and reassigned to %s. ' % (day, the_class,
                                                                                                  section, period,
                                                                                                  subject,
                                                                                                  teacher)
        except Exception as e:
            print('exception 09022020-A from timetable views.py %s %s' % (e.message, type(e)))
            print('%s class %s-%s period # %s is not yet assigned. Will be assigned now '
                  'This will be updated' % (day, the_class, section, period))
            tt = TimeTable(school=school, day=day, the_class=the_class, section=section, period=period)
            tt.subject = subject
            tt.teacher = teacher
            tt.save()
            message = '%s class %s-%s period # %s is now set to %s and assigned to %s. ' % (day, the_class,
                                                                                            section, period, subject,
                                                                                            teacher)
        print(message)

        # same entries in the Class Time Table ie CTimeTable
        print('repeating for the CTimeTable')
        try:
            ctt = CTimeTable.objects.get(school=school, day=day, the_class=the_class, section=section, period=period)
            print('%s class %s-%s period # %s is already set to %s and assigned to %s (in CTimeTable). '
                  'This will be updated' % (day, the_class, section, period, subject, teacher))
            ctt.subject = subject
            ctt.teacher = teacher
            ctt.save()
            message = '%s class %s-%s period # %s is now updated to %s and reassigned to %s. ' % (day, the_class,
                                                                                                  section, period,
                                                                                                  subject,
                                                                                                  teacher)
        except Exception as e:
            print('exception 09022020-B from timetable views.py %s %s' % (e.message, type(e)))
            print('%s class %s-%s period # %s is not yet assigned (in CTimeTable). Will be assigned now '
                  'This will be updated' % (day, the_class, section, period))
            ctt = CTimeTable(school=school, day=day, the_class=the_class, section=section, period=period)
            ctt.subject = subject
            ctt.teacher = teacher
            ctt.save()
            message = '%s class %s-%s period # %s is now set to %s and assigned to %s. ' % (day, the_class,
                                                                                            section, period, subject,
                                                                                            teacher)
        print(message)

        # set teacher period table
        try:
            tp = TeacherPeriods.objects.get(teacher=teacher, day=day, period=period)
            print('period %s for %s on %s is already set. This will be updated' % (period, teacher, day))
            tp.the_class = the_class
            tp.section = section
            tp.save()
            print('period %s for %s on %s is now updated' % (period, teacher, day))
        except Exception as e:
            print('exception 09022020-C from time_table views.py %s %s' % (e.message, type(e)))
            print('period %s for %s on %s is not yet set. This will be set' % (period, teacher, day))
            tp = TeacherPeriods(teacher=teacher, day=day, period=period)
            tp.the_class = the_class
            tp.section = section
            tp.save()
            print('period %s for %s on %s is now set' % (period, teacher, day))
        context_dict = {'message': message}
        return JSONResponse(context_dict, status=200)


class TheTimeTable(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = TimeTableSerializer

    def get(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Setup Time Table'
        form = ExcelFileUploadForm()
        context_dict['form'] = form
        return render(request, 'classup/setup_data.html', context_dict)

    def post(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Setup Time Table'

        # first see whether the cancel button was pressed
        if "cancel" in request.POST:
            return render(request, 'classup/setup_index.html', context_dict)

        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        # form = ExcelFileUploadForm(request.POST, request.FILES)
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for time table...')
                fileToProcess_handle = request.FILES['excelFile']

                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(fileToProcess_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
                sheet = fileToProcess.sheet_by_index(0)
                if sheet:
                    print ('Successfully got hold of sheet!')
                for row in range(sheet.nrows):
                    # first two rows are header rows
                    if row < 2:
                        continue
                    print ('Processing a new row')
                    t = sheet.cell(row, 1).value

                    # retrieve the teacher
                    if t != '':
                        print('retrieving teacher with id = %s' % t)
                        try:
                            teacher = Teacher.objects.get(school=school, email=t)
                            teacher_name = '%s %s' % (teacher.first_name, teacher.last_name)
                            print('successfull retrieved teacher for id %s: %s' % (t, teacher_name))
                        except Exception as e:
                            print('exception 21102018-A from time_table views.py %s %s' % (e.message, type(e)))
                            print('could not retrieve any teacher associated with %s' % t)
                            continue
                    try:
                        d = sheet.cell(row, 3).value
                        print('the_day = %s' % d)
                        print('setting time table for %s for %s' % (teacher_name, d))
                        day = DaysOfWeek.objects.get(day=d)
                        print('successfully retrieved the day object for %s' % d)
                        print(day)
                    except Exception as e:
                        print('failed to retrieved the day object for %s' % d)
                        print('exception 06032018-C fron time_table views.py' % (e.message, type(e)))

                    prd = 1
                    for counter in range(4, 27, 3):
                        period = Period.objects.get(school=school, period=prd)
                        print('setting period %s of %s for %s' % (prd, teacher_name, d))
                        col = counter
                        if col % 3 == 1:
                            try:
                                cls = sheet.cell(row, col).value
                                print('class mentioned in the sheet = %s' % cls)
                                # get the class object
                                if cls != '':
                                    the_class = Class.objects.get(school=school, standard=cls)
                                    print('retrieved class object associated with %s' % the_class)
                                    print(the_class)
                                col += 1
                                the_sec = sheet.cell(row, col).value
                                print('section mentioned in the sheet %s' % the_sec)

                                col += 1
                                sub = sheet.cell(row, col).value
                                print('subject mentioned in the sheet = %s' % sub)
                                if len(the_sec) > 0:
                                    print('period %s for %s subject %s multiple sections of class %s: %s' %
                                          (prd, teacher_name, sub, cls, the_sec))
                                    sec = the_sec.split()[0][0]
                                    print('only first section %s will be taken into account' % sec)
                                else:
                                    sec = the_sec
                                if sec != '':
                                    section = Section.objects.get(school=school, section=sec)
                                    print('retrieved section object associated with %s' % sec)
                                    print(section)
                                if sub != '':
                                    subject = Subject.objects.get(school=school, subject_name=sub)
                                    print('retrieved subject object associated with %s' % sub)
                                    print(subject)
                                else:
                                    if cls != '' and sec != '':
                                        subject = Subject.objects.get(school=school, subject_name='Main')

                                if cls != '':
                                    # assign the class, section, subject & period to the teacher
                                    try:
                                        tt = TimeTable.objects.get(school=school, day=day, period=period,
                                                                   teacher=teacher)
                                        print('period %i for %s was already assigned for %s. '
                                              'This will be updated...' % (prd, teacher_name, sub))
                                        tt.the_class = the_class
                                        tt.section = section
                                        tt.subject = subject
                                        tt.save()
                                        print('updated period %s on %s for teacher %s to '
                                              'subject %s, class %s-%s' %
                                              (prd, d, teacher_name, sub, cls, sec))

                                        # 14/02/2019 - now that we are using a separate table to store available
                                        # teachers, there are chances that this teacher could have been available
                                        # earlier, but now is engaged. Hence, need to be removed from the available
                                        # teacher table
                                        try:
                                            at = AvailableTeachers(school=school, day=day,
                                                                   period=period, teacher=teacher)
                                            print('%s was shown free for %s period %s' % (teacher, day, period))
                                            print('need to be removed from Available Teachers list')
                                            at.delete()
                                            print('now removed')
                                        except Exception as e:
                                            print('exception 14022019-A from time_table views.py %s %s' %
                                                  (e.message, type(e)))
                                            print('%s was not shown free for %s period %s' % (teacher, day, period))
                                    except Exception as e:
                                        print('exception 07032018-B from time_table views.py %s %s' % (
                                            e.message, type(e)))
                                        print('period %s on %s for teacher %s has not been assigned. '
                                              'Assigning now...' %
                                              (prd, d, teacher_name))
                                        tt = TimeTable(school=school, day=day, period=period, teacher=teacher)
                                        # 02/02/2019 - save so that juhior classes teachers are engaged. Because in
                                        # junior classes (LKG, UKG) there is no subject
                                        tt.the_class = the_class
                                        tt.section = section
                                        tt.subject = subject
                                        tt.save()
                                        print('assigned period %s on %s for teacher %s to subject %s, '
                                              'class %s-%s' % (prd, d, teacher_name, sub, cls, sec))
                                        # 14/02/2019 - now that we are using a separate table to store available
                                        # teachers, there are chances that this teacher could have been available
                                        # earlier, but now is engaged. Hence, need to be removed from the available
                                        # teacher table
                                        try:
                                            at = AvailableTeachers(school=school, day=day,
                                                                   period=period, teacher=teacher)
                                            print('%s was shown free for %s period %s' % (teacher, day, period))
                                            print('need to be removed from Available Teachers list')
                                            at.delete()
                                            print('now removed')
                                        except Exception as e:
                                            print('exception 14022019-A from time_table views.py %s %s' %
                                                  (e.message, type(e)))
                                            print('%s was not shown free for %s period %s' % (teacher, day, period))

                                    # 07/04/2018 - also make same entries in the ClassTimeTable
                                    if len(the_sec) > 1:
                                        print('dealing with multiple sections here %s' % the_sec)
                                    sec_list = list(the_sec)
                                    print('sec_list = ')
                                    print(sec_list)
                                    for sec in sec_list:
                                        if sec == '/':
                                            continue
                                        section = Section.objects.get(school=school, section=sec)
                                        try:
                                            ctt = CTimeTable.objects.get(school=school, day=day, period=period,
                                                                         section=section, teacher=teacher)
                                            print('CTimeTable period %i for %s was already assigned for %s. '
                                                  'This will be updated...' % (prd, teacher_name, sub))
                                            ctt.the_class = the_class
                                            ctt.section = section
                                            ctt.subject = subject
                                            ctt.save()
                                            print('updated period %s on %s for teacher %s to '
                                                  'subject %s, class %s-%s' %
                                                  (prd, d, teacher_name, sub, cls, sec))
                                        except Exception as e:
                                            print('exception 07032018-C from time_table views.py %s %s' % (
                                                e.message, type(e)))
                                            print('CTimeTable period %s on %s for teacher %s has not been assigned. '
                                                  'Assigning now...' %
                                                  (prd, d, teacher_name))
                                            ctt = CTimeTable(school=school, day=day,
                                                             period=period, teacher=teacher)
                                            ctt.the_class = the_class
                                            ctt.section = section
                                            ctt.subject = subject
                                            ctt.save()
                                            print('assigned period %s on %s for teacher %s to subject %s, '
                                                  'class %s-%s' % (prd, d, teacher_name, sub, cls, sec))

                                    # make entries in TeacherPeriod table
                                    # part II - each teacher's period assignment for every day
                                    try:
                                        tp = TeacherPeriods.objects.get(teacher=teacher, day=day,
                                                                        period=period)  # third
                                        print ('period %s for %s %s is already set. This will be updated' %
                                               (str(period), teacher.first_name, teacher.last_name))
                                        tp.the_class = the_class
                                        tp.section = section
                                        tp.save()
                                        print ('period %s for %s %s is updated' %
                                               (str(period), teacher.first_name, teacher.last_name))
                                    except Exception as e:
                                        print ('Exception 171117-D from time_table views.py %s %s' % (
                                            e.message, type(e)))
                                        print ('period %s for %s %s is not yet set. This will be set now' %
                                               (str(period), teacher.first_name, teacher.last_name))
                                        tp = TeacherPeriods(school=school, teacher=teacher, day=day,
                                                            period=period, the_class=the_class, section=section)
                                        try:
                                            tp.save()
                                            print ('period %s for %s %s is now set.' %
                                                   (str(period), teacher.first_name, teacher.last_name))
                                        except Exception as e:
                                            print ('exception 171117-E from time_table views.py %s %s' %
                                                   (e.message, type(e)))
                                            print ('failed to set period %s for %s %s ' %
                                                   (str(period), teacher.first_name, teacher.last_name))
                                else:
                                    if sub == '':  # because this can be a designated period for other work
                                        try:
                                            at = AvailableTeachers.objects.get(school=school,
                                                                               day=day, period=period, teacher=teacher)
                                            print(at)
                                            print('%s is alreay added to the available list for %s period %s' %
                                                  (teacher_name, day.day, period.period))

                                        except Exception as e:
                                            print('exception 13032019-A from timetable views.py %s %s' %
                                                  (e.message, type(e)))
                                            print('%s was not on the availability list on %s period %s. Adding...' %
                                                  (teacher_name, day.day, period.period))
                                            at = AvailableTeachers(school=school, day=day,
                                                                   period=period, teacher=teacher)
                                            at.save()
                                            print('%s is now on the availability list on %s period %s. Adding...' %
                                                  (teacher_name, day.day, period.period))
                            except Exception as e:
                                print('something went wrong while retrieving objects associated with %s %s %s' %
                                      (cls, sec, sub))
                                print('exception 07032018-A from time_table views.py %s %s' % (
                                    e.message, type(e)))
                        prd += 1

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request._request, 'time table successfully uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 06032018-A from time_table views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)

    def post1(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Setup Time Table'

        # first see whether the cancel button was pressed
        if "cancel" in request.POST:
            return render(request, 'classup/setup_index.html', context_dict)

        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for time table...')
                fileToProcess_handle = request.FILES['excelFile']

                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(fileToProcess_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
                sheet = fileToProcess.sheet_by_index(0)
                if sheet:
                    print ('Successfully got hold of sheet!')
                for row in range(sheet.nrows):
                    if row == 0:
                        continue
                    print ('Processing a new row')
                    the_day = sheet.cell(row, 0).value
                    print ('the_day = %s' % the_day)
                    the_class = sheet.cell(row, 1).value
                    print ('the_class = %s' % the_class)
                    the_section = sheet.cell(row, 2).value
                    print ('the_section = %s' % the_section)

                    for i in range(3, 11):
                        the_period = i - 2
                        teachers = sheet.cell(row, i).value
                        teacher_list = teachers.split('/')
                        for k in range(0, len(teacher_list)):
                            teacher_id = teacher_list[k]
                            print ('teacher_id = %s' % teacher_id)
                            try:
                                teacher = Teacher.objects.get(school=school, email=teacher_id)
                                c = Class.objects.get(school=school, standard=the_class)
                                section = Section.objects.get(school=school, section=the_section)
                                day = DaysOfWeek.objects.get(day=the_day)
                                period = Period.objects.get(school=school, period=str(the_period))

                                # part I - class wise period assignment for every day
                                try:
                                    tt_entry = TimeTable.objects.get(school=school, day=day, the_class=c,
                                                                     section=section, period=period)
                                    print ('period %s for class %s-%s is already assigned to %s %s. '
                                           'This will be updated.' %
                                           (str(period), the_class, the_section,
                                            tt_entry.teacher.first_name, tt_entry.teacher.last_name))
                                    tt_entry.teacher = teacher
                                    tt_entry.save()
                                    print ('updated period %s for class %s %s to %s %s' %
                                           (str(period), the_class, the_section,
                                            tt_entry.teacher.first_name, tt_entry.teacher.last_name))
                                except Exception as e:
                                    print ('Exception 171117-A from time_table view.py %s %s' % (e.message, type(e)))
                                    print ('period %s for class %s-%s is not set. Setting it now...' %
                                           (str(period), the_class, the_section))
                                    tt_entry = TimeTable(school=school, day=day, the_class=c,
                                                         section=section, period=period, teacher=teacher)
                                    tt_entry.save()
                                    print ('period %s for class %s %s now assigned to %s %s' %
                                           (str(period), the_class, the_section,
                                            teacher.first_name, teacher.last_name))

                                # part II - each teacher's period assignment for every day
                                try:
                                    tp = TeacherPeriods.objects.get(teacher=teacher, day=day, period=period)  # third
                                    print ('period %s for %s %s is already set. This will be updated' %
                                           (str(the_period), teacher.first_name, teacher.last_name))
                                    tp.the_class = c
                                    tp.section = section
                                    tp.save()
                                    print ('period %s for %s %s is updated' %
                                           (str(the_period), teacher.first_name, teacher.last_name))
                                except Exception as e:
                                    print ('Exception 171117-D from time_table views.py %s %s' % (e.message, type(e)))
                                    print ('period %s for %s %s is not yet set. This will be set now' %
                                           (str(the_period), teacher.first_name, teacher.last_name))
                                    tp = TeacherPeriods(school=school, teacher=teacher, day=day, period=period,
                                                        the_class=c, section=section)
                                    try:
                                        tp.save()
                                        print ('period %s for %s %s is now set.' %
                                               (str(the_period), teacher.first_name, teacher.last_name))
                                    except Exception as e:
                                        print ('exception 171117-E from time_table views.py %s %s' %
                                               (e.message, type(e)))
                                        print ('failed to set period %s for %s %s ' %
                                               (str(the_period), teacher.first_name, teacher.last_name))
                            except Exception as e:
                                print('exception 171117-B from time_table views.py %s %s' % (e.message, type(e)))
                                print ('teacher was %s' % teacher_list[k])

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request._request, 'time table successfully uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 171117-C from time_table views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)


class TheTeacherPeriod(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Period Load on Teachers'

        excel_file_name = 'Teacher_Period_Details.xlsx'
        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Teacher Periods")

        header = workbook.add_format({
            'bold': True,
            'bg_color': '#F7F7F7',
            'color': 'black',
            'align': 'center',
            'valign': 'top',
            'border': 1
        })
        cell_center = workbook.add_format({
            'text_wrap': True,
        })
        row = 2
        sheet.write(row, 0, ugettext("S No."), header)
        sheet.write(row, 1, ugettext("Teacher"), header)
        sheet.write(row, 2, ugettext("Day"), header)
        sheet.write(row, 3, ugettext("I"), header)
        sheet.write(row, 4, ugettext("II"), header)
        sheet.write(row, 5, ugettext("III"), header)
        sheet.write(row, 6, ugettext("IV"), header)
        sheet.write(row, 7, ugettext("V"), header)
        sheet.write(row, 8, ugettext("VI"), header)
        sheet.write(row, 9, ugettext("VII"), header)
        sheet.write(row, 10, ugettext("VIII"), header)
        sheet.write(row, 11, ugettext("Total"), header)
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 6)
        sheet.set_column('D:K', 9)

        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        teachers = Teacher.objects.filter(school=school).order_by('first_name')
        row = 3
        s_no = 1
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for t in teachers:
            teacher_name = t.first_name + ' ' + t.last_name
            sheet.write_number(row, 0, s_no)
            sheet.write_string(row, 1, teacher_name)
            week_total = 0
            for d in days:
                sheet.write_string(row, 2, d)
                day = DaysOfWeek.objects.get(day=d)
                day_total = 0
                for i in range(1, 9):
                    period = Period.objects.get(school=school, period=str(i))
                    try:
                        tt = TimeTable.objects.get(teacher=t, day=day, period=period)  # first occurrence
                        the_class = tt.the_class.standard
                        section = tt.section.section
                        subject = tt.subject.subject_name
                        class_sec_sub = '%s-%s \n(%s)' % (the_class, section, subject)
                        sheet.write_string(row, i + 2, class_sec_sub, cell_center)
                        day_total = day_total + 1
                        week_total = week_total + 1

                    except Exception as e:
                        print ('exception 191117-A from time_table views.py %s %s' % (e.message, type(e)))
                        print ('period %i on %s is free for %s' % (i, d, teacher_name))
                        if d == 'Saturday' and i > 6:
                            sheet.write_string(row, i + 2, "N/A")
                        else:
                            sheet.write_string(row, i + 2, "Free")
                    sheet.write_number(row, i + 2 + 1, day_total)
                row = row + 1
            sheet.write_number(row, i + 2 + 1, week_total, header)
            row += 2
            sheet.write(row, 1, ugettext("Teacher"), header)
            sheet.write(row, 2, ugettext("Day"), header)
            sheet.write(row, 3, ugettext("I"), header)
            sheet.write(row, 4, ugettext("II"), header)
            sheet.write(row, 5, ugettext("III"), header)
            sheet.write(row, 6, ugettext("IV"), header)
            sheet.write(row, 7, ugettext("V"), header)
            sheet.write(row, 8, ugettext("VI"), header)
            sheet.write(row, 9, ugettext("VII"), header)
            sheet.write(row, 10, ugettext("VIII"), header)
            sheet.write(row, 11, ugettext("Total"), header)
            row += 1
            s_no = s_no + 1

        workbook.close()

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response


class TheTeacherWingMapping(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = TeacherWingMappingSerializer

    def get(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Teacher Wing Mapping'
        form = ExcelFileUploadForm()
        context_dict['form'] = form
        return render(request, 'classup/setup_data.html', context_dict)

    def post(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Teacher Wing Mapping'

        # first see whether the cancel button was pressed
        if "cancel" in request.POST:
            return render(request, 'classup/setup_index.html', context_dict)

        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for teacher wing mapping...')
                fileToProcess_handle = request.FILES['excelFile']

                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(fileToProcess_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
                sheet = fileToProcess.sheet_by_index(0)
                if sheet:
                    print ('Successfully got hold of sheet!')
                for row in range(sheet.nrows):
                    if row == 0:
                        continue
                    print ('Processing a new row')
                    login = sheet.cell(row, 0).value
                    w = sheet.cell(row, 1).value
                    print ('teacher login  = %s' % login)
                    try:
                        teacher = Teacher.objects.get(email=login)
                        print ('teacher = %s %s' % (teacher.first_name, teacher.last_name))
                        wing = Wing.objects.get(school=school, wing=w)
                        print ('wing = %s' % wing.wing)

                        try:
                            mapping = TeacherWingMapping.objects.get(teacher=teacher, wing=wing)
                            print ('teacher %s %s was already mapped to %s. This will be updated' %
                                   (teacher.first_name, teacher.last_name, wing.wing))
                            mapping.teacher = teacher
                            mapping.wing = wing
                            mapping.save()
                            print ('mapping for teacher %s %s updated to %s. ' %
                                   (teacher.first_name, teacher.last_name, wing.wing))
                        except Exception as e:
                            print ('Exception 201117-B from time_table views.py %s %s' % (e.message, type(e)))
                            print ('wing mapping for %s %s not done. Will be done now...' %
                                   (teacher.first_name, teacher.last_name))
                            mapping = TeacherWingMapping(school=school, teacher=teacher, wing=wing)
                            mapping.save()
                            print ('%s %s mapped to %s' % (teacher.first_name, teacher.last_name, w))
                    except Exception as e:
                        print ('exception 201117-A from time_table views.py %s %s' % (e.message, type(e)))
                        print ('either teacher or wing could not be determined')

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request._request, 'Teacher Wing Mapping successfully uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 201117-C from time_table views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)


class AbsentTeacherPeriods(generics.ListAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        start_time = time.time()
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Arrangement Processing'
        context_dict['csrf_token'] = 'csrf_token'
        school_id = request.session['school_id']
        context_dict['school_id'] = school_id
        school = School.objects.get(id=school_id)
        today = datetime.datetime.today()
        d = calendar.day_name[today.weekday()]
        print ('day = %s' % d)
        day = DaysOfWeek.objects.get(day=d)

        try:
            # get the default excluded list
            excluded_list = []
            excluded = ExcludedFromArrangements1.objects.filter(school=school)
            for e in excluded:
                excluded_list.append(e.teacher.email)
                print (excluded_list)
            ta = TeacherAttendance.objects.filter(school=school, date=today)
            print ('ta = ')
            print (ta)

            # all the teachers who are absent today, should also be part of excluded list
            for t in ta:
                excluded_list.append(t.teacher)
            print ('excluded list including today absent teachers: ')
            print (excluded_list)
            context_dict['excluded_list'] = excluded_list

            # for all the absent teachers today, we need to identify the periods which they take
            arrangements_required = []
            for t in ta:
                absent_teacher = t.teacher
                teacher_name = absent_teacher.first_name + ' ' + absent_teacher.last_name

                # get the period list that this teacher was supposed to take today
                try:
                    teacher_periods = TimeTable.objects.filter(teacher=absent_teacher,
                                                               day=day).order_by('period__period')
                    print ('periods = ')
                    print (teacher_periods)
                    for tp in teacher_periods:
                        arrangement_unit = {}
                        arrangement_unit['teacher'] = teacher_name
                        the_class = tp.the_class
                        arrangement_unit['the_class'] = the_class.standard
                        section = tp.section
                        arrangement_unit['section'] = section.section
                        period = tp.period
                        arrangement_unit['period'] = period.period

                        # 05/01/2018 - check if any arrangement has already been made for this period
                        try:
                            record = Arrangements.objects.get(school=school, date=datetime.date.today(),
                                                              the_class=the_class, section=section, period=period)
                            substitute_teacher = record.teacher.first_name + ' ' + record.teacher.last_name
                            # print ('substitute teacher %s has already been assigned for period %s of class %s-%s' %
                            #       (substitute_teacher, str(period.period), the_class.standard, section.section))
                            arrangement_unit['substitute_teacher'] = substitute_teacher
                        except Exception as e:
                            print ('exception 05012018-A from time_table views.py %s %s' % (e.message, type(e)))
                            print ('substitute teacher has not been assigned for period %s of class %s-%s' %
                                   (str(period.period), the_class.standard, section.section))
                            arrangement_unit['substitute_teacher'] = 'Not Assigned'

                        arrangements_required.append(arrangement_unit)
                        print ('at this stage arrangements_required = ')
                        print (arrangements_required)
                except Exception as e:
                    print ('exception 211117-A from time_table views.py %s %s' % (e.message, type(e)))
                    print ('looks like %s %s had no periods today' % (absent_teacher.first_name,
                                                                      absent_teacher.last_name))
            context_dict['arrangements_required'] = arrangements_required

            # get the list of available teachers from first to last period
            available_list = {}
            periods = Period.objects.all()
            teacher_load = {

            }
            for period in periods:
                print('getting list of available teachers for %s period %s' % (day, period))
                # now, find which teacher is free on this period
                available = []
                try:
                    available_teachers = AvailableTeachers.objects.filter(school=school, day=day, period=period)
                    for a_teacher in available_teachers:
                        if a_teacher.teacher not in excluded_list:
                            this_teacher = {}
                            print('%s is available today ie %s for period %s' % (a_teacher.teacher, day, period))
                            if a_teacher not in teacher_load:
                                periods_count = TeacherPeriods.objects.filter(teacher=a_teacher.teacher,
                                                                              day=day).count()
                                teacher_load[a_teacher.teacher] = periods_count
                            else:
                                periods_count = teacher_load[a_teacher.teacher]
                            this_teacher["login_id"] = str(a_teacher.teacher.email)
                            this_teacher["name"] = '%s %s (%i)' % \
                                                   (a_teacher.teacher.first_name,
                                                    a_teacher.teacher.last_name, periods_count)
                            available.append(this_teacher)
                            available_list[str(period.period)] = available
                except Exception as e:
                    print('exception 13012019-B from time_table view.py %s %s' % (e.message, type(e)))
                    print('failed to retrieve list of availabl teacher for %s period %s' % (day, period))

            context_dict['available_teachers'] = available_list
            print("---time taken %s seconds ---" % (time.time() - start_time))

            return render(request, 'classup/arrangements.html', context_dict)
        except Exception as e:
            print ('exception 31122017-A from time_table views.py %s %s' % (e.message, type(e)))
            response = HttpResponse(status=201)
            return response


class GenerateEntrySheet(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)
        excel_file_name = 'TimeTable.xlsx'
        print (excel_file_name)
        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Teacher Wise Time Table")
        sheet.freeze_panes(2, 4)

        header = workbook.add_format({
            'bold': True,
            'bg_color': '#F7F7F7',
            'color': 'black',
            'align': 'center',
            'valign': 'top',
            'border': 1
        })
        sheet.merge_range('A1:A2', 'S No', header)
        sheet.merge_range('B1:C1', 'Teacher Details', header)
        sheet.merge_range('D1:D2', 'Day', header)
        sheet.merge_range('E1:G1', 'I', header)
        sheet.merge_range('H1:J1', 'II', header)
        sheet.merge_range('K1:M1', 'III', header)
        sheet.merge_range('N1:P1', 'IV', header)
        sheet.merge_range('Q1:S1', 'V', header)
        sheet.merge_range('T1:V1', 'VI', header)
        sheet.merge_range('W1:Y1', 'VII', header)
        sheet.merge_range('Z1:AB1', 'VIII', header)

        sheet.write_string(1, 1, 'ID', header)
        sheet.write_string(1, 2, 'Name', header)
        row = 1
        col = 4
        for period in range(1, 9):
            sheet.write_string(row, col, 'Class', header)
            col = col + 1
            sheet.write_string(row, col, 'Sec', header)
            col = col + 1
            sheet.write_string(row, col, 'Subject', header)
            col = col + 1
        row = row + 1
        col = 0
        sr_no = 1
        teacher_list = Teacher.objects.filter(school=school, active_status=True).order_by('first_name')
        for teacher in teacher_list:
            sheet.write_string(row, col, str(sr_no))
            col = col + 1
            sheet.write_string(row, col, teacher.email)
            col = col + 1
            teacher_name = teacher.first_name + ' ' + teacher.last_name
            sheet.write_string(row, col, teacher_name)
            col = col + 1
            days = DaysOfWeek.objects.all()
            for day in days:
                if day.day != 'Sunday':
                    sheet.write_string(row, col, day.day)
                    row = row + 1
            col = 0
            sr_no = sr_no + 1

        workbook.close()

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response


class GetArrangements(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Arrangement Processing'
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)
        today = datetime.datetime.today()

        stirng_date = today.strftime('%d-%m-%Y')
        excel_file_name = 'Arrangements_' + stirng_date + '.xlsx'
        print (excel_file_name)
        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Absent Teacher Wise")
        sheet2 = workbook.add_worksheet("Substitute Teacher Wise")

        title = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })

        sheet.write(0, 3, 'Arrangements for %s' % stirng_date, title)
        sheet2.write(0, 3, ('Teacher Wise Arrangements for %s' % stirng_date), title)

        width = 20
        sheet.set_column('B:B', width)
        sheet.set_column('F:F', width)
        sheet.set_column('G:G', width)
        sheet.set_column('H:H', width)
        sheet.set_column('I:I', width)
        sheet.set_column('J:J', width)

        sheet2.set_column('B:B', width)
        sheet2.set_column('F:F', width)
        sheet2.set_column('G:G', width)
        sheet2.set_column('H:H', width)
        sheet2.set_column('I:I', width)
        sheet2.set_column('J:J', width)

        header = workbook.add_format({
            'bold': True,
            'bg_color': '#F7F7F7',
            'color': 'black',
            'align': 'center',
            'valign': 'top',
            'border': 1
        })

        row = 2
        sheet.write(row, 0, ugettext("S No."), header)
        sheet.write(row, 1, ugettext("Absent Teacher"), header)
        sheet.write(row, 2, ugettext("Period"), header)
        sheet.write(row, 3, ugettext("Class"), header)
        sheet.write(row, 4, ugettext("Section"), header)
        sheet.write(row, 5, ugettext("Substitute Teacher"), header)

        # get the list of absent teachers
        try:
            row = row + 1

            ta = TeacherAttendance.objects.filter(school=school, date=today).order_by('teacher__first_name')
            print (ta)
            s_no = 1
            for t in ta:
                sheet.write_number(row, 0, s_no)
                d = calendar.day_name[today.weekday()]
                print ('day = %s' % d)
                day = DaysOfWeek.objects.get(day=d)
                absent_teacher = t.teacher
                teacher_name = absent_teacher.first_name + ' ' + absent_teacher.last_name
                sheet.write_string(row, 1, teacher_name)

                # get the period list that this teacher was supposed to take today
                try:
                    teacher_periods = CTimeTable.objects.filter(teacher=absent_teacher,
                                                                day=day).order_by('period__period')  # second
                    print ('periods = ')
                    print (teacher_periods)
                    for tp in teacher_periods:
                        period = tp.period
                        sheet.write_string(row, 2, period.period)
                        the_class = tp.the_class
                        sheet.write_string(row, 3, the_class.standard)
                        section = tp.section
                        sheet.write_string(row, 4, section.section)

                        # see if an arrangement has been made for this period
                        try:
                            print(school)
                            print(today)
                            print(period)
                            print(the_class)
                            print(section)
                            arrangement = Arrangements.objects.get(school=school, date=today, period=period,
                                                                   the_class=the_class, section=section)
                            substitute_teacher = arrangement.teacher.first_name + ' ' + arrangement.teacher.last_name
                            sheet.write_string(row, 5, substitute_teacher)
                        except Exception as e:
                            print ('exception 06012018-D from time_table views.py %s %s' % (e.message, type(e)))
                            print ('arrangement not carried out for period %s, class %s-%s of %s' %
                                   (period.period, the_class.standard, section.section, teacher_name))
                            sheet.write_string(row, 5, 'Not Assigned')
                        row = row + 1
                except Exception as e:
                    print ('exception 211117-A from time_table views.py %s %s' % (e.message, type(e)))
                    print ('looks like %s %s had no periods today' % (absent_teacher.first_name,
                                                                      absent_teacher.last_name))
                s_no = s_no + 1
        except Exception as e:
            print ('exception 211117-B from time_table views.py %s %s' % (e.message, type(e)))

        # now, get the report substitute teacher wise
        row = 2
        sheet2.write(row, 0, ugettext("S No."), header)
        sheet2.write(row, 1, ugettext("Substitute Teacher"), header)
        sheet2.write(row, 2, ugettext("Period"), header)
        sheet2.write(row, 3, ugettext("Class"), header)
        row = row + 1

        try:
            s_no = 1
            arrangements = Arrangements.objects.filter(school=school, date=today).order_by('teacher__first_name')
            for arrangement in arrangements:
                substitute_teacher = arrangement.teacher.first_name + ' ' + arrangement.teacher.last_name
                sheet2.write_string(row, 0, str(s_no))
                sheet2.write_string(row, 1, substitute_teacher)
                sheet2.write_string(row, 2, arrangement.period.period)
                class_sec = arrangement.the_class.standard + '-' + arrangement.section.section
                sheet2.write_string(row, 3, class_sec)
                row = row + 1
                s_no = s_no + 1
            workbook.close()

            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
            response.write(output.getvalue())
            return response
        except Exception as e:
            print ('exception 06012018-E from time_table views.py %s %s' % (e.message, type(e)))
            print ('No arrangements today')
            workbook.close()
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
            response.write(output.getvalue())
            return response


class SetArrangements(generics.ListCreateAPIView):
    # we will be reading the excel file which will be uploaded and store the arrangements in the db.
    # We will also write to an excel file which will contain the details of each arrangement periods.
    # School will download this file and paste at various notice boards and also keep in file for record purpose

    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Set Arrangement Periods'
        form = ExcelFileUploadForm()
        context_dict['form'] = form
        return render(request, 'classup/setup_data.html', context_dict)

    def post(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['header'] = 'Set Arrangement Periods'

        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        print ('setting arragnements for %s' % school.school_name)

        print('request=')
        print(request.body)
        try:
            data = json.loads(request.body)
            print ('json=')
            print (data)
            p = data['period']
            period = Period.objects.get(school=school, period=p)
            tc = data['the_class']
            the_class = Class.objects.get(school=school, standard=tc)
            s = data['section']
            section = Section.objects.get(school=school, section=s)
            t = data['teacher']
            teacher = Teacher.objects.get(email=t)
            new_teacher = teacher.first_name + ' ' + teacher.last_name
            try:
                record = Arrangements.objects.get(school=school, date=datetime.date.today(),
                                                  the_class=the_class, section=section, period=period)
                current_teacher = record.teacher.first_name + ' ' + record.teacher.last_name
                print ('arrangement for period # %s of class %s-%s was already assinged to %s. '
                       'Need to send cancellation message...' % (p, tc, s, current_teacher))
                message = 'Dear %s, arrangement assignment for period %s class %s-%s is cancelled' % \
                          (current_teacher, p, tc, s)
                print (message)
                mobile = record.teacher.mobile
                # sms.send_sms1(school, 'admin (web interface', mobile, message, 'Arrangement Cancellation')
                record.teacher = teacher
                record.save()
                print ('arrangement for period # %s of class %s-%s is now assinged to: %s.' % (p, tc, s, new_teacher))
                return HttpResponse(status=200)
            except Exception as e:
                print ('exception 05012018-C from time_table views.py %s %s' % (e.message, type(e)))
                print ('arrangement for period # %s of class %s-%s was not assigned. Will be done now...' % (p, tc, s))
                arrangement = Arrangements(school=school, date=datetime.date.today(),
                                           the_class=the_class, section=section, period=period, teacher=teacher)
                arrangement.save()
                print ('arrangement for period # %s of class %s-%s is now assinged to: %s.' % (p, tc, s, new_teacher))
                return HttpResponse(status=200)

        except Exception as e:
            print ('failed to load json from request')
            print ('Exception 05012018-B from time_table views.py %s %s' % (e.message, type(e)))
            return HttpResponse(status=201)


class NotifyArrangements(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['header'] = 'Set Arrangement Periods'

        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        print ('setting arragnements for %s' % school.school_name)

        print('request=')
        print(request.body)
        try:
            data = json.loads(request.body)
            print ('json=')
            print (data)

            recepient = data['recepient']
            if recepient == 'single':
                p = data['period']
                period = Period.objects.get(school=school, period=p)
                tc = data['the_class']
                the_class = Class.objects.get(school=school, standard=tc)
                s = data['section']
                section = Section.objects.get(school=school, section=s)

                # get the teacher assigned for arrangement for this period/class/section
                try:
                    arrangement = Arrangements.objects.get(school=school, date=datetime.date.today(),
                                                           period=period, the_class=the_class, section=section)
                    teacher = arrangement.teacher
                    name = teacher.first_name + ' ' + teacher.last_name
                    message = 'Dear %s, today you have to take arrangement for period no %s in class %s-%s' % \
                              (name, p, tc, s)
                    print (message)
                    sms.send_sms1(school, "admin (web interface)", teacher.mobile, message, "Arrangment Notification")
                    return HttpResponse(status=200)
                except Exception as e:
                    print ('exception 06012018-B from time_table views.py %s %s' % (e.message, type(e)))
                    print ('failed to retrieve arrangement details for period # %s in class %s-%s' % (p, tc, s))
                    return HttpResponse(status=201)
            else:
                try:
                    arrangements = Arrangements.objects.filter(school=school, date=datetime.date.today())
                    for arrangement in arrangements:
                        teacher = arrangement.teacher
                        p = arrangement.period.period
                        tc = arrangement.the_class.standard
                        s = arrangement.section.section

                        name = teacher.first_name + ' ' + teacher.last_name
                        message = 'Dear %s, today you have to take arrangement for period %s in class %s-%s' % \
                                  (name, p, tc, s)
                        print (message)
                        sms.send_sms1(school, "admin (web interface)", teacher.mobile,
                                      message, "Arrangment Notification")
                    return HttpResponse(status=200)
                except Exception as e:
                    print ('exception 06012018-C from time_table views.py %s %s' % (e.message, type(e)))
                    print ('failed to retrieve arrangement details for school: %s in class %s-%s' %
                           (school.school_name))
                    return HttpResponse(status=201)
        except Exception as e:
            print ('failed to load json from request')
            print ('Exception 06012018-A from time_table views.py %s %s' % (e.message, type(e)))
            return HttpResponse(status=201)


class ClassTimeTable(generics.ListAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Download Time Table for a Class'

        if request.session['user_type'] == 'school_admin':
            context_dict['user_type'] = 'school_admin'

        school_id = request.session['school_id']
        form = ResultSheetForm(school_id=school_id)
        context_dict['form'] = form
        return render(request, 'classup/student_list.html', context_dict)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Download Time Table for a Class'

        if request.session['user_type'] == 'school_admin':
            context_dict['user_type'] = 'school_admin'
        if "cancel" in request.POST:
            return render(request, 'classup/student_list.html', context_dict)
        else:
            school_id = request.session['school_id']
            school = School.objects.get(id=school_id)
            print(school)
            school_name = school.school_name
            school_name = school_name.replace(' ', '_')
            print(school_name)
            form = ResultSheetForm(request.POST, school_id=school_id)

            if form.is_valid():
                the_class = form.cleaned_data['the_class']
                print(the_class)
                section = form.cleaned_data['section']
                print(section)
                print ('Time Table will be generated for %s-%s' % (the_class.standard, section.section))

                excel_file_name = '%s_Time_Table_%s-%s.xlsx' % (str(school_name),
                                                                str(the_class.standard), str(section.section))
                output = StringIO.StringIO(excel_file_name)
                workbook = xlsxwriter.Workbook(output)
                sheet = workbook.add_worksheet('Time Table %s-%s' % (str(the_class.standard), section.section))

                border = workbook.add_format()
                border.set_border()

                title = workbook.add_format({
                    'bold': True,
                    'font_size': 14,
                    'align': 'center',
                    'valign': 'vcenter'
                })

                cell_normal = workbook.add_format({
                    'align': 'left',
                    'valign': 'top',
                    'text_wrap': True
                })
                cell_normal.set_border()
                cell_center = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'text_wrap': True,
                    'bold': True
                })
                cell_center.set_border()

                heading = 'Time Table for %s-%s' % (the_class, section)
                sheet.merge_range('B1:J1', heading, title)
                sheet.set_column('A:A', 2)
                sheet.set_column('B:B', 9)
                sheet.set_column('C:J', 12)

                # set the border
                for row in range(2, 9):
                    for col in range(1, 10):
                        sheet.write(row, col, '', border)
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                sequence = ['1', '2', '3', '4', '5', '6', '7', '8']
                period = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII']

                row = 2
                col = 1
                sheet.write_string(row, col, 'Day', cell_center)
                col += 1
                for p in period:
                    sheet.write_string(row, col, p, cell_center)
                    col += 1
                row += 1
                col = 1
                for d in days:
                    day = DaysOfWeek.objects.get(day=d)
                    sheet.write_string(row, col, d, cell_center)
                    col += 1
                    for seq in sequence:
                        try:
                            period = Period.objects.filter(school=school, period=seq)
                            tt = CTimeTable.objects.get(school=school, day=day, period=period,
                                                        the_class=the_class, section=section)
                            subject = tt.subject.subject_name
                            teacher = '%s %s' % (tt.teacher.first_name, tt.teacher.last_name)
                            print('on %s, period %s in class %s-%s is of subject %s taken by %s' %
                                  (d, seq, the_class.standard, section.section, subject, teacher))
                            entry = '%s\n(%s)' % (subject, teacher)
                            sheet.write_string(row, col, entry, cell_normal)
                            col += 1
                        except Exception as e:
                            print('failed to retrieve the time table details of %s period %s class %s-%s' %
                                  (d, seq, the_class.standard, section.section))
                            print('exception 07042018-A from time_table views.py %s %s' % (e.message, type(e)))
                            # see if multiple teachers are assigned (in case of subjects like music)
                            try:
                                tt = CTimeTable.objects.filter(school=school, day=day, period=period,
                                                               the_class=the_class, section=section)

                                if tt.count() > 0:
                                    print(tt)
                                    print('multiple teacher assignment case')
                                    tt = tt[:1].get()
                                    subject = tt.subject.subject_name
                                    teacher = '%s %s' % (tt.teacher.first_name, tt.teacher.last_name)
                                    print('on %s, period %s in class %s-%s is of subject %s taken by %s' %
                                          (d, seq, the_class.standard, section.section, subject, teacher))
                                    entry = '%s\n(%s)' % (subject, teacher)
                                    sheet.write_string(row, col, entry, cell_normal)
                            except Exception as e:
                                print('%s period %s for class %s-%s is not set' %
                                      (d, seq, the_class.standard, section.section))
                                print('exception 07042018-E from time_table views.py %s %s' % (e.message, type(e)))
                            col += 1
                    row += 1
                    col = 1
                workbook.close()
                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
                response.write(output.getvalue())
                return response
            else:
                error = 'You have missed to select either Class, or Section'
                form = ResultSheetForm(request)
                context_dict['form'] = form
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/student_list.html', context_dict)
