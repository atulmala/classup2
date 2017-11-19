import xlrd

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt

from authentication.views import JSONResponse, log_entry
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics

from setup.forms import ExcelFileUploadForm

from setup.views import validate_excel_extension

from teacher.models import Teacher

from .serializers import *


from .models import *

# Create your views here.


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening



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


def setup_time_table (request):
    context_dict = {

    }
    context_dict['user_type'] = 'school_admin'
    context_dict['school_name'] = request.session['school_name']

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Setup Time Table'
    if request.method == 'POST':
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
                    the_class = sheet.cell (row, 1).value
                    print ('the_class = %s' % the_class)
                    the_section = sheet.cell (row, 2).value
                    print ('the_section = %s' % the_section)

                    for i in range(3, 11):
                        the_period = i-2
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
                                    tt_entry = TimeTable.objects.get (school=school, day=day, the_class=c,
                                                                      section=section, period=period)
                                    print ('period %s for class %s-%s is already assigned to %s %s. '
                                           'This will be updated.' %
                                           (str (period), the_class, the_section,
                                            tt_entry.teacher.first_name, tt_entry.teacher.last_name))
                                    tt_entry.teacher = teacher
                                    tt_entry.save ()
                                    print ('updated period %s for class %s %s to %s %s' %
                                           (str (period), the_class, the_section,
                                            tt_entry.teacher.first_name, tt_entry.teacher.last_name))
                                except Exception as e:
                                    print ('Exception 171117-A from time_table view.py %s %s' % (e.message, type(e)))
                                    print ('period %s for class %s-%s is not set. Setting it now...' %
                                           (str(period), the_class, the_section))
                                    tt_entry = TimeTable(school=school, day=day, the_class=c,
                                                         section=section, period=period, teacher=teacher)
                                    tt_entry.save()
                                    print ('period %s for class %s %s now assigned to %s %s' %
                                           (str (period), the_class, the_section,
                                            teacher.first_name, teacher.last_name))

                                # part II - each teacher's period assignment for every day
                                try:
                                    tp = TeacherPeriods.objects.get (teacher=teacher, day=day, period=period)
                                    print ('period %s for %s %s is already set. This will be updated' %
                                           (str (the_period), teacher.first_name, teacher.last_name))
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

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'time table successfully uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 171117-C from time_table views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)





