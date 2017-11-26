import xlrd
import StringIO
import xlsxwriter
import datetime
import calendar

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation import ugettext

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics

from setup.forms import ExcelFileUploadForm

from setup.views import validate_excel_extension

from teacher.models import TeacherAttendance

from operations import sms

from .serializers import *
from .models import *

# Create your views here.


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class ArrangementListForTeachers (generics.ListAPIView):
    serializer_class = ArrangementSerializer

    def get_queryset(self):
        email = self.kwargs['teacher']
        teacher = Teacher.objects.get (email=email)
        q = Arrangements.objects.filter (teacher=teacher, date=datetime.datetime.today()).order_by ('period')
        return q


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
                                    tp = TeacherPeriods.objects.get(teacher=teacher, day=day, period=period)
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


class TheTeacherPeriod (generics.ListAPIView):
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

        sheet.write(2, 0, ugettext("S No."), header)
        sheet.write(2, 1, ugettext("Teacher"), header)
        sheet.write(2, 2, ugettext("Day"), header)
        sheet.write(2, 3, ugettext("1"), header)
        sheet.write(2, 4, ugettext("2"), header)
        sheet.write(2, 5, ugettext("3"), header)
        sheet.write(2, 6, ugettext("4"), header)
        sheet.write(2, 7, ugettext("5"), header)
        sheet.write(2, 8, ugettext("6"), header)
        sheet.write(2, 9, ugettext("7"), header)
        sheet.write(2, 10, ugettext("8"), header)
        sheet.write(2, 11, ugettext("Total"), header)

        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        Teachers = Teacher.objects.filter (school=school).order_by('first_name')
        row = 3
        s_no = 1
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for t in Teachers:
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
                        tp = TeacherPeriods.objects.get(teacher=t, day=day, period=period)
                        the_class = tp.the_class.standard
                        section = tp.section.section
                        class_sec = the_class + '-' + section
                        sheet.write_string (row, i+2, class_sec)
                        day_total = day_total + 1
                        week_total = week_total + 1

                    except Exception as e:
                        print ('exception 191117-A from time_table views.py %s %s' % (e.message, type(e)))
                        print ('period %i on %s is free for %s' % (i, d, teacher_name))
                        if d == 'Saturday' and i > 6:
                            sheet.write_string(row, i + 2, "N/A")
                        else:
                            sheet.write_string(row, i + 2, "Free")
                    sheet.write_number (row, i+2+1, day_total)
                row = row + 1
            sheet.write_number (row, i+2+1, week_total, header)
            row = row + 2
            s_no = s_no + 1

        workbook.close()

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response


class TheTeacherWingMapping (generics.ListCreateAPIView):
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
                    w = sheet.cell (row, 1).value
                    print ('teacher login  = %s' % login)
                    try:
                        teacher = Teacher.objects.get (email=login)
                        print ('teacher = %s %s' % (teacher.first_name, teacher.last_name))
                        wing = Wing.objects.get (school=school, wing=w)
                        print ('wing = %s' % wing.wing)

                        try:
                            mapping = TeacherWingMapping.objects.get (teacher=teacher, wing=wing)
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


class GetArrangements (generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Arrangement Processing'
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)
        today = datetime.datetime.today()

        stirng_date = today.strftime('%d_%m_%Y')
        excel_file_name = 'Arrangements_' + stirng_date + '.xlsx'
        print (excel_file_name)
        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Arrangements")
        width = 20
        sheet.set_column('B:B', width)
        sheet.set_column('F:F', width)
        sheet.set_column('G:G', width)
        sheet.set_column('H:H', width)
        sheet.set_column('I:I', width)
        sheet.set_column('J:J', width)

        header = workbook.add_format({
            'bold': True,
            'bg_color': '#F7F7F7',
            'color': 'black',
            'align': 'center',
            'valign': 'top',
            'border': 1
        })

        row = 0
        sheet.write(row, 0, ugettext("S No."), header)
        sheet.write(row, 1, ugettext("Absent Teacher"), header)
        sheet.write(row, 2, ugettext("Class"), header)
        sheet.write(row, 3, ugettext("Section"), header)
        sheet.write(row, 4, ugettext("Period"), header)
        sheet.write(row, 5, ugettext("Substitute Teacher"), header)
        sheet.merge_range('G1:I1', ugettext("Suggested Teachers For Substitution"), header)

        # get the list of absent teachers
        try:
            row = row + 1
            excluded_list = []
            excluded = ExcludedFromArrangements1.objects.filter(school=school)
            for e in excluded:
                excluded_list.append(e.teacher.email)
                print (excluded_list)
            ta = TeacherAttendance.objects.filter(school=school, date=today)

            # all the teachers who are absent today, should also be part of excluded list
            for t in ta:
                excluded_list.append(t.teacher.email)
            print ('excluded list including today absent teachers: ')
            print (excluded_list)
            print (ta)
            s_no = 1
            for t in ta:
                sheet.write_number (row, 0, s_no)
                d = calendar.day_name[today.weekday()]
                print ('day = %s' % d)
                day = DaysOfWeek.objects.get (day=d)
                absent_teacher = t.teacher
                teacher_name = absent_teacher.first_name + ' ' + absent_teacher.last_name
                sheet.write_string(row, 1, teacher_name)

                # get the period list that this teacher was supposed to take today
                try:
                    teacher_periods = TeacherPeriods.objects.filter(teacher=absent_teacher, day=day)
                    print ('periods = ')
                    print (teacher_periods)
                    for tp in teacher_periods:
                        the_class = tp.the_class
                        sheet.write_string(row, 2, the_class.standard)
                        section = tp.section
                        sheet.write_string(row, 3, section.section)
                        period = tp.period
                        sheet.write_string(row, 4, period.period)

                        # now, find which teacher is free on this period
                        col = 6
                        all_teachers = Teacher.objects.filter (school=school).order_by ('first_name')
                        for a_teacher in all_teachers:
                            if a_teacher.email not in excluded_list:
                                print ('now checking %s %s availability for period # %s on %s' %
                                       (a_teacher.first_name, a_teacher.last_name, period.period, d))
                                try:
                                    engaged = TeacherPeriods.objects.get (teacher=a_teacher, day=day, period=period)
                                    if engaged:
                                        print ('%s %s is not available on %s for period: %s' %
                                               (a_teacher.first_name, a_teacher.last_name, d, period.period))
                                    else:
                                        print ('%s %s is available on %s for period: %s. will be added to available list' %
                                               (a_teacher.first_name, a_teacher.last_name, d, period.period))
                                except Exception as e:
                                    print ('exception 211117-P from time_table views.py %s %s' %
                                           (e.message, type(e)))
                                    print ('%s %s is available on %s for period: %s. will be added to available list'
                                           % (a_teacher.first_name, a_teacher.last_name, d, str (period.period)))
                                    teacher_login_id = a_teacher.email
                                    sheet.write_string (row, col, teacher_login_id)
                                    col = col + 1
                            else:
                                print ('%s %s is in excluded list. Hence not being considered for Arrangements'
                                       % (a_teacher.first_name, a_teacher.last_name))
                        row = row + 1
                except Exception as e:
                    print ('exception 211117-A from time_table views.py %s %s' % (e.message, type(e)))
                    print ('looks like %s %s had no periods today' % (absent_teacher.first_name,
                                                                      absent_teacher.last_name))
                s_no = s_no + 1
            row = row + 1
            workbook.close()

            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
            response.write(output.getvalue())
            return response
        except Exception as e:
            print ('exception 211117-B from time_table views.py %s %s' % (e.message, type(e)))
            workbook.close()
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
            response.write(output.getvalue())
            return response


class SetArrangements (generics.ListCreateAPIView):
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
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Set Arrangement Periods'

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
                today = datetime.datetime.today()
                stirng_date = today.strftime('%d_%m_%Y')
                string_date1 = today.strftime('%d-%m-%Y')
                d = calendar.day_name[today.weekday()]
                print ('now starting to set arrangements for %s %s...' % (d, stirng_date))
                excel_file_name = 'Arrangements_' + stirng_date + '.xlsx'
                print (excel_file_name)
                output = StringIO.StringIO(excel_file_name)
                workbook = xlsxwriter.Workbook(output)
                output_sheet = workbook.add_worksheet("Arrangements")
                width = 20
                output_sheet.set_column('B:B', width)
                output_sheet.set_column('F:F', width)

                title = workbook.add_format({
                    'bold': True,
                    'font_size': 14,
                    'align': 'center',
                    'valign': 'vcenter'
                })
                header = workbook.add_format({
                    'bold': True,
                    'bg_color': '#F7F7F7',
                    'color': 'black',
                    'align': 'center',
                    'valign': 'top',
                    'border': 1
                })

                title_text = 'Arrangements for ' + d + ', ' + stirng_date
                output_sheet.merge_range('A0:L0', title_text, title)
                output_row = 2

                output_sheet.write(output_row, 0, ugettext("S No."), header)
                output_sheet.write(output_row, 1, ugettext("Absent Teacher"), header)
                output_sheet.write(output_row, 2, ugettext("Class"), header)
                output_sheet.write(output_row, 3, ugettext("Section"), header)
                output_sheet.write(output_row, 4, ugettext("Period"), header)
                output_sheet.write(output_row, 5, ugettext("Substitute Teacher"), header)
                output_row = output_row + 1

                fileToProcess_handle = request.FILES['excelFile']

                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(fileToProcess_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
                input_sheet = fileToProcess.sheet_by_index(0)
                if input_sheet:
                    print ('Successfully got hold of sheet!')
                for input_row in range(input_sheet.nrows):
                    if input_row == 0:
                        continue
                    print ('Processing a new row')

                    s_no_raw = input_sheet.cell(input_row, 0).value
                    output_sheet.write(output_row, 0, s_no_raw)

                    absent_teacher = input_sheet.cell (input_row, 1).value
                    output_sheet.write_string (output_row, 1, absent_teacher)

                    the_class = input_sheet.cell(input_row, 2).value
                    c = Class.objects.get (school=school, standard=the_class)
                    output_sheet.write_string(output_row, 2, the_class)
                    section = input_sheet.cell(input_row, 3).value
                    s = Section.objects.get (school=school, section=section)
                    output_sheet.write_string(output_row, 3, section)

                    period = input_sheet.cell(input_row, 4).value
                    p = Period.objects.get (school=school, period=period)
                    output_sheet.write(output_row, 4, ugettext(period))

                    substitute_teacher = input_sheet.cell(input_row, 5).value
                    try:
                        t = Teacher.objects.get(email=substitute_teacher)
                        substitute_teacher_name = t.first_name + ' ' + t.last_name

                        # store the arrangement in db and send sms to the teacher
                        try:
                            arrangement = Arrangements.objects.get(date=today,
                                                                   the_class=c, section=s, period=p)
                            old_teacher = arrangement.teacher
                            old_teacher_name = old_teacher.first_name + ' ' + old_teacher.last_name
                            old_teacher_email = arrangement.teacher.email

                            # send cancellation SMS to the old teacher (only if the new teacher != old teacher
                            if old_teacher_email != t.email:
                                message = 'Dear ' + old_teacher_name
                                message += ', Today (' + string_date1 + '), arrangement in class '
                                message += the_class + '-' + section + ' in period ' + period + ' is cancelled.'
                                message += '. Regards, Academics Coordinator'
                                print (message)

                                mobile = old_teacher.mobile
                                sender = request.session['user']
                                sms.send_sms1(school, sender, mobile, message, 'Arrangement Period Assignment')
                                print ('arrangement cancellation SMS sent to %s' % (old_teacher))

                                print ('arrangement for %s-%s for period # %s was assigned to %s. It will be updated' %
                                       (the_class, section, period, old_teacher))
                                arrangement.teacher = t
                                arrangement.save()
                                print ('arrangement for %s-%s for period # %s re-assigned to %s %s. ' %
                                       (the_class, section, period, t.first_name, t.last_name))

                                message = 'Dear ' + t.first_name + ' ' + t.last_name
                                message += ', Today (' + string_date1 + '), you have to take arrangement in class '
                                message += the_class + '-' + section + ' in period ' + period
                                message += '. Regards, Academics Coordinator'
                                print (message)

                                mobile = t.mobile
                                sender = request.session['user']
                                sms.send_sms1(school, sender, mobile, message, 'Arrangement Period Assignment')
                                print ('arrangement period SMS sent to %s %s' % (t.first_name, t.last_name))
                            else:
                                print ('no change in Arrangement. Hence doing nothing...')
                        except Exception as e:
                            print ('exception 221117-Y from time_table views.py %s %s' % (e.message, type(e)))
                            print ('arrangement for %s-%s for period # %s not yet set. It will be set now' %
                                   (the_class, section, period))
                            arrangement = Arrangements(school=school, teacher=t, date=today,
                                                       the_class=c, section=s, period=p)
                            arrangement.save()
                            print ('arrangement for %s-%s for period # %s assigned to %s %s. ' %
                                   (the_class, section, period, t.first_name, t.last_name))
                            message = 'Dear ' + t.first_name + ' ' + t.last_name
                            message += ', Today (' + string_date1 + '), you have to take arrangement in class '
                            message += the_class + '-' + section + ' in period ' + period
                            message += '. Regards, Academics Coordinator'
                            print (message)

                            mobile = t.mobile
                            sender = request.session['user']
                            sms.send_sms1(school, sender, mobile, message, 'Arrangement Period Assignment')
                            print ('arrangement period SMS sent to %s %s' % (t.first_name, t.last_name))

                    except Exception as e:
                        print ('exception 221117-Z from time_table view.py %s %s' % (e.message, type(e)))
                        substitute_teacher_name = 'Not Assigned'
                    output_sheet.write_string(output_row, 5, substitute_teacher_name)
                    print ('point E')

                    output_row = output_row + 1

                workbook.close()
                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request._request, 'Arrangements Processed')
                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
                response.write(output.getvalue())
                return response
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 221117-B from time_table views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)