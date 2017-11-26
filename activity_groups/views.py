import xlrd

from django.shortcuts import render

from django.contrib import messages

from rest_framework import generics

from setup.forms import ExcelFileUploadForm
from setup.views import validate_excel_extension

from student.serializers import StudentSerializer

from .serializers import *

# Create your views here.


class ActivityMembersManager (generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Setup Activity Group Members   '
        form = ExcelFileUploadForm()
        context_dict['form'] = form
        return render(request, 'classup/setup_data.html', context_dict)

    def post(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Setup Activity Group'

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
                print ('now starting to process the uploaded file Activity Group members setup...')
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
                        print ('checking for existence of group...')
                        group_name = sheet.cell (row, 0).value
                        print ('group_name = %s' % group_name)
                        try:
                            activity_group = ActivityGroup.objects.get (school=school, group_name=group_name)
                            print ('activity group %s in school %s already exists' % (group_name, school.school_name))
                        except Exception as e:
                            print ('activity group %s does not exist at %s', (group_name, school.school_name))
                            print ('exception 241117-A from activity_group views.py %s %s', (e.message, type(e)))
                            error = 'Activity Group does not exist.'
                            print (error)
                            form.errors['__all__'] = form.error_class([error])
                            return render(request, 'classup/setup_data.html', context_dict)

                    print ('Processing a new row')
                    erp_id = sheet.cell(row, 0).value
                    print ('erp_id = %s. Will now try to add to Activity Group %s' % (erp_id, group_name))
                    try:
                        student = Student.objects.get (school=school, student_erp_id=erp_id)
                        try:
                            entry, created = ActivityMembers.objects.get_or_create(
                                group=activity_group,
                                student=student
                            )
                            if entry:
                                print ('student %s %s is already a member of %s group' %
                                       (student.fist_name, student.last_name, group_name))
                            if created:
                                print ('made student %s %s a member of %s group' %
                                       (student.fist_name, student.last_name, group_name))
                        except Exception as e:
                            print ('exception 241117-C from activity_group views.py %s %s' % (e.message, type(e)))
                            print ('could not create an Activity Group entry for student with erp_id %s in %s' %
                                   (erp_id, activity_group))
                    except Student.DoesNotExist as e:
                        print ('no student is associated with erp_id %s' % erp_id)
                        print ('exception 241117-B from activity_group views.py %s %s' % (e.message, type(e)))
                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request._request, 'Activity Group entries created.')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 171117-C from time_table views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)


class ActivityGroupList (generics.ListAPIView):
    serializer_class = ActivityGroupSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get (id=school_id)
        q = ActivityGroup.objects.filter (school=school).order_by ('group_name')
        return q


class ActivityGroupMembersList (generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        group = ActivityGroup.objects.filter (id=group_id)
        q = Student.objects.filter(activitymembers__group=group, active_status=True).order_by('fist_name')
        return q




