import os
import datetime
import xlrd

from rest_framework import generics
from django.views.decorators.csrf import csrf_exempt

from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from setup.forms import ExcelFileUploadForm

from setup.models import School, UserSchoolMapping
from academics.models import Class, Section, Subject, WorkingDays, TestResults, ClassTest, ClassTeacher, Exam
from teacher.models import Teacher
from student.models import Student, Parent
from .models import Configurations

from .serializers import ConfigurationSerializer

from operations import sms

server_ip = 'http://52.32.99.184/'
router_server_ip = 'http://52.32.99.184/'
update_marks_list = False


# function to validate the extension of uploaded excel file - should be either .xls or .xlsx
def validate_excel_extension(file_handle, form, context_dict):
    print ('Inside validate_excel_extension function...')
    (file_name, file_extension) = os.path.splitext(str(file_handle))
    print ('file extension = ' + file_extension)
    if file_extension != '.xls' and file_extension != '.xlsx':
        # this is not a file with either .xls or .xlsx extension.
        error = 'The file you uploaded is not a valid excel file. '
        error += 'Expecting an excel file with extension .xls or .xlsx '
        error += 'You have uploaded ' + str(file_handle) + '. Please try again.'
        form.errors['__all__'] = form.error_class([error])
        context_dict['error'] = error
        print (error)
        return False
    else:
        return True

# Create your views here.


def setup_index(request):
    response = render(request, 'classup/setup_index.html')
    return response

@csrf_exempt
def setup_students(request):
    context_dict = {

    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Student Data'

    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                # determine the school for which this processing is done
                school_id = request.session['school_id']
                school = School.objects.get(id=school_id)
                print('school=' + school.school_name)
                print ('now starting to process the uploaded file for setting up Student data...')
                file_to_process_handle = request.FILES['excelFile']

                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(file_to_process_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                file_to_process = xlrd.open_workbook(filename=None, file_contents=file_to_process_handle.read())
                sheet = file_to_process.sheet_by_index(0)
                if sheet:
                    print ('Successfully got hold of sheet!')
                for row in range(sheet.nrows):
                    # skip the header row
                    if row == 0:
                        continue
                    print ('Processing a new row')
                    # first, capture student data
                    # we need to explicitly cast student id to string. Else update will not function properly
                    student_id = str(sheet.cell(row, 0).value)
                    student_first_name = sheet.cell(row, 1).value
                    student_last_name = sheet.cell(row, 2).value
                    current_class = sheet.cell(row, 3).value
                    current_section = sheet.cell(row, 4).value
                    current_roll_no_raw = sheet.cell(row, 5).value

                    # excel may add a decimal to the roll number. We need to convert it to integer
                    current_roll_no = int(current_roll_no_raw)
                    print (current_roll_no_raw)
                    print (current_roll_no)

                    # now, capture the parent data
                    parent_name = sheet.cell(row, 6).value
                    parent_email = sheet.cell(row, 7).value
                    # we need to explicitly cast mobile number to string. Else update will not function properly
                    parent_mobile1_raw = sheet.cell(row, 8).value
                    parent_mobile2_raw = sheet.cell(row, 9).value

                    # excel can put a decimal followed by zero in mobile numbers. This needs to be fixed
                    parent_mobile1 = int(parent_mobile1_raw)

                    # mobile 2 can be blank
                    if parent_mobile2_raw != '':
                        parent_mobile2 = int(parent_mobile2_raw)
                    else:
                        parent_mobile2 = 1234567890

                    # create parent into database
                    try:
                        p = Parent.objects.get(parent_mobile1=parent_mobile1)

                        if p:
                            print ('Parent ' + parent_name + ' already exist. This will be updated!')
                            p.parent_name = parent_name
                            p.parent_mobile1 = parent_mobile1
                            p.parent_mobile2 = parent_mobile2
                            p.parent_email = parent_email
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('Parent ' + parent_name + ' is a new entry. This will be created!')
                        p = Parent(parent_name=parent_name, parent_mobile1=parent_mobile1,
                                   parent_mobile2=parent_mobile2, parent_email=parent_email)
                    try:
                        p.save()
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        error = 'Unable to save the parent data for ' + parent_name + ' in Table Parent'
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        continue
                    # now, create a user for this parent

                    user = None
                    whether_new_user = False
                    try:
                        if User.objects.filter(username=parent_mobile1).exists():
                            print('user for parent ' + p.parent_name + ' already exists!')
                            whether_new_user = False
                        else:
                            whether_new_user = True
                            # the user name would be the mobile, and password would be a random string
                            password = User.objects.make_random_password(length=5, allowed_chars='1234567890')

                            print ('Initial password = ' + password)
                            user = User.objects.create_user(parent_mobile1, parent_email, password)
                            user.first_name = parent_name
                            user.is_staff = False
                            user.save()

                            print ('Successfully created user for ' + parent_name)
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('Unable to create user for ' + parent_name)
                        # todo implement the code to send password to the user through an sms and email

                    try:
                        conf = Configurations.objects.get(school=school)
                        if whether_new_user:
                            android_link = conf.google_play_link
                            iOS_link = conf.app_store_link

                            # send login id and password to parent via sms
                            message = 'Dear Ms/Mr ' + parent_name + ', thanks for registering at ' \
                                                                    'ClassUp(TM) mobile app. '
                            message += "Now you can track your child's progress at " + school.school_name + ' '
                            message += 'using ClassUp App. '
                            message += 'Please install ClassUp from these links. Android: '
                            message += android_link
                            message += ' iPhone/iOS: '
                            message += iOS_link
                            message += ' Your user id is: ' + str(parent_mobile1) + ', and password is: ' + password
                            message += '. You can change your password after first login. '
                            message += 'In case of any problem please send an email to: info@classup.in'
                            print(message)

                            sms.send_sms(parent_mobile1, message)
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('Failed to create Parent School mapping for ' + parent_name + ' in ClassUpRouter')

                    # now, start creating the student. The parent created above will be the parent of this student.

                    # class and section are foreign keys. Get hold of the relevant objects
                    print ('Class = ' + current_class)

                    try:
                        the_class = Class.objects.get(school=school, standard=current_class)
                    except Exception as e:
                        error = 'Unable to retrieve the relevant class: ' + current_class
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        # todo - we should skip this student but report this and move on to the next student <provide code>
                        continue

                    try:
                        the_section = Section.objects.get(school=school, section=current_section)
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        error = 'Unable to retrieve the relevant object for section: ' + current_section
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        # todo - we should skip this student but report this and move on to the next student <provide code>
                        continue

                    # process student. If this is an existing student, this is an update operations.
                    try:
                        s = Student.objects.get(school=school, student_erp_id=student_id)
                        if s:
                            print ('Student with  ID: ' + student_id + ' & name: ' + student_first_name + ' in school '
                                   + school.school_name + ' already exists. This will be updated!')
                            s.student_erp_id = student_id
                            s.fist_name = student_first_name
                            s.last_name = student_last_name
                            s.current_class = the_class
                            s.current_section = the_section
                            if s.roll_number != current_roll_no:
                                global update_marks_list
                                update_marks_list = True
                            s.roll_number = current_roll_no
                            s.parent = p
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('Student with ID:  ' + student_id + ' Name: '
                               + student_first_name + ' ' + student_last_name +
                               ' is a new entry for school ' + school.school_name + '. Hence inserting...')
                        try:
                            s = Student(school=school, student_erp_id=student_id, fist_name=student_first_name,
                                        last_name=student_last_name,
                                        current_class=the_class, current_section=the_section,
                                        roll_number=current_roll_no, parent=p)
                            s.save()
                            print ('saving successful!')
                            # this student should appear in all the pending test for this class & section
                            print ('creating an entry for this student in all pending test for this class/section')
                            try:
                                tests = ClassTest.objects.filter(the_class=the_class,
                                                                 section=the_section, is_completed=False)
                                for t in tests:
                                    test_result = TestResults(class_test=t, roll_no=current_roll_no,
                                                              student=s, marks_obtained=-5000.00, grade='')
                                    try:
                                        test_result.save()
                                        print (' test results successfully created')
                                    except Exception as e:
                                        print ('failed to create test results')
                                        print ('Exception = %s (%s)' % (e.message, type(e)))
                            except Exception as e:
                                print ('Currently no pending tests for this class/section')
                                print ('Exception = %s (%s)' % (e.message, type(e)))
                        except Exception as e:
                            error = 'Unable to create the new student in the database'
                            print (error)
                            print ('Exception = %s (%s)' % (e.message, type(e)))
                            form.errors['__all__'] = form.error_class([error])
                            # todo - we should skip this student but report this and move on to the next student <provide code>
                    try:
                        s.save()
                        print ('updated Student with  ID: ' + student_id + ' & name: ' + student_first_name)

                        # 04/01/2016 - if the roll number has been changed, we need to update the marks entry list
                        if update_marks_list:
                            print ('going to update the roll number')
                            try:
                                results = TestResults.objects.filter(student=s, class_test__is_completed=False)
                                for r in results:
                                    r.roll_no = current_roll_no
                                    try:
                                        r.save()
                                        print ('roll number updated in test_result')
                                    except Exception as e:
                                        print ('unable to change roll number in test result')
                                        print ('Exception = %s (%s)' % (e.message, type(e)))
                            except Exception as e:
                                print ('no pending tests for which roll number needs to be changed')
                                print ('Exception = %s (%s)' % (e.message, type(e)))
                            update_marks_list = False
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        error = 'Unable to save the data for Student with ID: ' + student_id + \
                                ' Name: ' + student_first_name + ' ' + student_last_name + ' in Table Student'
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        # todo - we should skip this student but report this and move on to the next student <provide code>

                # file upload and saving to db was successful. Hence go back to the main menu
                print ('reached here')
                print (context_dict)
                messages.success(request, 'Student Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_classes(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Class Data'
    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                # determine the school for which this processing is done
                school_id = request.session['school_id']
                school = School.objects.get(id=school_id)
                print('school=' + school.school_name)
                print ('now starting to process the uploaded file for setting up Classes...')
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
                    class_standard = sheet.cell(row, 0).value
                    class_sequence = sheet.cell(row, 1).value
                    print(class_standard)
                    print(class_sequence)

                    # Now we are ready to insert into db. But, we need to be sure that we are not trying
                    # to insert a duplicate
                    try:
                        c = Class.objects.get(school=school, standard=class_standard, sequence=class_sequence)
                        if c:
                            print('Class ' + class_standard + ' for school ' + school.school_name +
                                  ' already exist. Hence skipping...')
                    except Exception as e:
                        print('Exception = %s (%s)' % (e.message, type(e)))
                        print('class ' + class_standard + ' is a new class. Hence inserting...')
                        try:
                            c = Class(standard=class_standard)
                            c.school = school
                            c.sequence = class_sequence
                            c.save()
                        except Exception as e:
                            print ('Exception = %s (%s)' % (e.message, type(e)))
                            error = 'Unable to save the class ' + class_standard + ' in table Class'
                            form.errors['__all__'] = form.error_class([error])
                            print(error)
                            return render(request, 'classup/setup_data.html', context_dict)

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Classes Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print('Exception = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print(error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        # we are arriving at this page for the first time, hence show an empty form
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_sections(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Section Data'
    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                school_id = request.session['school_id']
                school = School.objects.get(id=school_id)
                print('now starting to process the uploaded file for setting up Sections...')
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
                    section = sheet.cell(row, 0).value
                    print (section)

                    # Now we are ready to insert into db. But, we need to be sure that we are not trying
                    # to insert a duplicate
                    try:
                        s = Section.objects.get(school=school, section=section)
                        if (s):
                            print ('Section ' + section + 'for school ' + school.school_name
                                   + ' already exist. Hence skipping...')
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('Section ' + section + ' is a new section. Hence inserting...')
                        try:
                            s = Section(section=section)
                            s.school = school
                            s.save()
                        except Exception as e:
                            print ('Exception = %s (%s)' % (e.message, type(e)))
                            error = 'Unable to save the data in Table Section'
                            form.errors['__all__'] = form.error_class([error])
                            print (error)
                            return render(request, 'classup/setup_data.html', context_dict)
                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Section Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_teachers(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Teachers Data'
    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                school_id = request.session['school_id']
                school = School.objects.get(id=school_id)

                print ('now starting to process the uploaded file for setting up Teachers...')
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
                    # skip the header row
                    if row == 0:
                        continue
                    print ('Processing a new row')
                    # we need to explicitly cast employee id to string. Else update will not function properly
                    employee_id = str(sheet.cell(row, 0).value)
                    f_name = sheet.cell(row, 1).value
                    l_name = sheet.cell(row, 2).value
                    email = sheet.cell(row, 3).value

                    # we need to explicitly case mobile number to string. Else update will not function properly
                    mobile_raw = sheet.cell(row, 4).value
                    mobile_int = int(mobile_raw)
                    mobile = str(mobile_int)

                    # if this is an existing employee/teacher, this is an update operations.
                    try:
                        t = Teacher.objects.get(school=school, teacher_erp_id=employee_id)

                        if t:
                            print ('Teacher with Employee ID: ' + employee_id +
                                   ' & name: ' + f_name + ' already exist. This will be updated!')
                            t.first_name = f_name
                            t.last_name = l_name
                            t.email = email
                            t.mobile = mobile
                            try:
                                t.save()
                                print ('Teacher ' + f_name + ' ' + l_name + ' ' + 'updated')
                            except Exception as e:
                                print ('Updating ' + f_name + ' ' + l_name + ' ' + 'failed!')
                                print ('Exception = %s (%s)' % (e.message, type(e)))

                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('Teacher ' + f_name + ' ' + l_name + ' is a new entry. Hence inserting...')
                        t = Teacher(teacher_erp_id=employee_id, school=school, first_name=f_name, last_name=l_name,
                                    email=email, mobile=mobile)
                        try:
                            t.save()
                            print ('Successfully created Teacher ' + f_name + ' ' + l_name)

                            # now, create a user for this teacher
                            # the user name would be the email, and password would be a random string
                            password = User.objects.make_random_password(length=5, allowed_chars='1234567890')

                            print ('Initial password = ' + password)
                            user = None
                            try:
                                user = User.objects.create_user(email, email, password)
                                user.first_name = f_name
                                user.last_name = l_name
                                user.is_staff = True
                                user.save()
                                print ('Successfully created user for ' + f_name + ' ' + l_name)

                                mapping = UserSchoolMapping(user=user, school=school)
                                mapping.save()
                            except Exception as e:
                                print ('Exception = %s (%s)' % (e.message, type(e)))
                                print ('Unable to create user or user-school mapping for ' + f_name + ' ' + l_name)
                            # todo implement the code to send password to the user through an sms and email

                            # make this user part of the Teachers group
                            try:
                                group = Group.objects.get(name='teachers')
                                user.groups.add(group)
                                print ('Successfully added ' + f_name + ' ' + l_name + ' to the Teachers group')
                            except Exception as e:
                                print ('Exception = %s (%s)' % (e.message, type(e)))
                                print ('Unable to add ' + f_name + ' ' + l_name + ' to the Teachers group')

                            # get the links of app on Google Play and Apple App store
                            configuration = Configurations.objects.get(school=school)
                            android_link = configuration.google_play_link
                            iOS_link = configuration.app_store_link

                            # send login id and password to teacher via sms
                            message = 'Dear ' + f_name + ' ' + l_name + ', thanks for registering at ClassUp(TM).'
                            message += 'Please install ClassUp from these links. Android: '
                            message += android_link
                            message += ', iPhone/iOS: '
                            message += iOS_link
                            message += '. Your user id is: ' + email + ', and password is: ' + password + '. '
                            message += 'You can change your password after first login. '
                            message += 'Enjoy managing your class with ClassUp!'
                            message += ' In case of any problem please send an email to: info@classup.in'

                            sms.send_sms(mobile, message)

                        except Exception as e:
                            print ('Exception = %s (%s)' % (e.message, type(e)))
                            error = 'Unable to save the data for ' + f_name + ' ' + l_name + ' in Table Teacher'
                            form.errors['__all__'] = form.error_class([error])
                            print (error)
                            # todo - we should skip this teacher but report this and move on to the next treacher <provide code>
                            continue

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Teacher Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_subjects(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Subjects Data'
    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                school_id = request.session['school_id']
                school = School.objects.get(id=school_id)

                print ('now starting to process the uploaded file for setting up Subjects...')
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
                    # skip the header row
                    if row == 0:
                        continue
                    print ('Processing a new row')
                    # we need to explicitly cast employee id to string. Else update will not function properly
                    sub_name = str(sheet.cell(row, 0).value)
                    sub_code = sheet.cell(row, 1).value
                    sub_sequence = sheet.cell(row, 2).value

                    # if this is an existing subject, this is an update operations.
                    try:
                        s = Subject.objects.get(school=school, subject_code=sub_code)
                        if s:
                            print ('Subject: ' + sub_name + ' already exist. This will be updated!')
                            s.subject_name = sub_name
                            s.subject_code = sub_code
                            s.subject_sequence = sub_sequence
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('Subject ' + sub_name + ' is a new entry. Hence inserting...')
                        s = Subject(school=school, subject_name=sub_name,
                                    subject_code=sub_code, subject_sequence=sub_sequence)
                    try:
                        s.save()
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        error = 'Unable to save the data for ' + sub_name + ' ' + sub_code + ' in Table Subject'
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Subjects Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_working_days(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)
        return HttpResponseRedirect(reverse('setup_index'))

    # now start processing the file upload

    context_dict['header'] = 'Upload Working Days'
    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print 'now starting to process the uploaded file for setting up Working Days...'
                fileToProcess_handle = request.FILES['excelFile']

                # check that the file uploaded should be a valid excel
                # file with .xls or .xlsx
                if not validate_excel_extension(fileToProcess_handle, form, context_dict):
                    return render(request, 'classup/setup_data.html', context_dict)

                # if this is a valid excel file - start processing it
                fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
                sheet = fileToProcess.sheet_by_index(0)
                if sheet:
                    print 'Successfully got hold of sheet!'
                for row in range(sheet.nrows):
                    if row == 0:
                        continue
                    print 'Processing a new row'

                    y = sheet.cell(row, 0).value
                    print ('year=' + str(int(y)))

                    m = sheet.cell(row, 1).value
                    print('month=' + str(int(m)))

                    d = sheet.cell(row, 2).value
                    print('days=' + str(int(d)))

                    # Now we are ready to insert into db. But, we need to be sure that we are not trying
                    # to insert a duplicate
                    try:
                        wd = WorkingDays.objects.get(year=y, month=m)
                        if wd:
                            print 'working days for ' + str(int(y)) + '/' + str(int(m)) + \
                                  ' already set. This will be updated...'
                            wd.working_days = d
                            try:
                                wd.save()
                                print 'successfully updated working days for ' + str(int(y)) + '/' + str(int(m))
                            except Exception as e:
                                print 'unable to update working days for ' + str(int(y)) + '/' + str(int(m))
                                print 'Exception = %s (%s)' % (e.message, type(e))

                    except Exception as e:
                        print 'Exception = %s (%s)' % (e.message, type(e))
                        print 'working days for ' + str(int(y)) + '/' + str(int(m)) + \
                              ' are not yet set. Setting them now...'
                        try:
                            wd = WorkingDays(year=y, month=m, working_days=d)
                            wd.save()
                            print 'successfully set working days for ' + str(int(y)) + '/' + str(int(m))
                        except Exception as e:
                            print 'unable to set working days for ' + str(int(y)) + '/' + str(int(m))
                            print 'Exception = %s (%s)' % (e.message, type(e))
                            error = 'unable to set working days for ' + str(int(y)) + '/' + str(int(m))
                            form.errors['__all__'] = form.error_class([error])
                            print error
                            return render(request, 'classup/setup_data.html', context_dict)

                # file upload and saving to db was successful. Hence go back to the main menu
                return render(request, 'classup/setup_index.html', context_dict)
                return HttpResponseRedirect(reverse('setup_index'))
            except Exception as e:
                print 'Exception = %s (%s)' % (e.message, type(e))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print error
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_class_teacher(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Class Teacher Details'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for setting up Class Teachers...')
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

                    the_class = sheet.cell(row, 0).value

                    section = sheet.cell(row, 1).value

                    class_teacher = sheet.cell(row, 2).value

                    # Now we are ready to insert into db. But, we need to be sure that we are not trying
                    # to insert a duplicate
                    try:
                        c = Class.objects.get(school=school, standard=the_class)
                        s = Section.objects.get(school=school, section=section)
                        t = Teacher.objects.get(teacher_erp_id=class_teacher)
                        ct = ClassTeacher.objects.get(standard=c, section=s)
                        if ct:
                            print ('class teacher for ' + the_class + '-' + section +
                                   ' already set. This will be updated...')
                            ct.class_teacher = t
                            try:
                                ct.save()
                                print ('successfully updated class teacher ' + the_class + '-' + section)
                            except Exception as e:
                                print ('unable to the update class teacher for ' + the_class + '-' + section)
                                print ('Exception = %s (%s)' % (e.message, type(e)))
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('class teacher for ' + the_class + '-' + section +
                               ' is not yet set. Setting them now...')
                        try:
                            c = Class.objects.get(school=school, standard=the_class)
                            s = Section.objects.get(school=school, section=section)
                            t = Teacher.objects.get(teacher_erp_id=class_teacher)
                            ct = ClassTeacher(school=school, standard=c, section=s, class_teacher=t)
                            ct.save()
                            print ('successfully class teacher for ' + the_class + '-' + section)
                        except Exception as e:
                            print ('unable to set class teacher for ' + the_class + '-' + section)
                            print ('Exception = %s (%s)' % (e.message, type(e)))
                            error = ('unable to set class teacher ' + the_class + '-' + section)
                            form.errors['__all__'] = form.error_class([error])
                            print (error)
                            return render(request, 'classup/setup_data.html', context_dict)

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Class Teachers Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_exam(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Exam Details'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for setting up Exams...')
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

                    exam_title = sheet.cell(row, 0).value
                    print (exam_title)

                    esd = sheet.cell(row, 1).value
                    exam_start_date = datetime.datetime(*xlrd.xldate_as_tuple(esd, fileToProcess.datemode))
                    print (exam_start_date)

                    eed = sheet.cell(row, 2).value
                    exam_end_date = datetime.datetime(*xlrd.xldate_as_tuple(eed, fileToProcess.datemode))
                    print (exam_end_date)
                    exam_start_class = sheet.cell(row, 3).value
                    print (exam_start_class)
                    exam_end_class = sheet.cell(row, 4).value
                    print (exam_end_class)

                    # Now we are ready to insert into db. But, we need to be sure that we are not trying
                    # to insert a duplicate

                    try:
                        e = Exam.objects.get(school=school, title=exam_title, start_class=exam_start_class,
                                             end_class=exam_end_class)

                        if e:
                            print ('Exam ' + exam_title + ' for ' + exam_start_class + ' and ' + exam_end_class
                                   + ' already set. This will be updated...')
                            e.start_date = exam_start_date
                            e.end_date = exam_end_date
                            try:
                                e.save()
                                print ('successfully updated Exam ' + exam_title)
                            except Exception as e:
                                print ('unable to the update Exam ' + exam_title)
                                print ('Exception = %s (%s)' % (e.message, type(e)))

                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('Exam  ' + exam_title + ' for ' + exam_start_class + ' and ' +
                               exam_end_class + ' is not yet set. Setting it now...')
                        try:
                            e = Exam(school=school, title=exam_title, start_date=exam_start_date,
                                     end_date=exam_end_date, start_class=exam_start_class, end_class=exam_end_class)
                            e.save()
                            print ('successfully created Exam  ' + exam_title + ' with start date: '
                                   + str(exam_start_date) + ' and end date: ' + str(exam_end_date) +
                                   ' for ' + exam_start_class + ' and ' + exam_end_class)
                        except Exception as e:
                            print ('unable to create exam ' + exam_title + ' with start date: '
                                   + str(exam_start_date) + ' and end date: ' + str(exam_end_date) + ' for ' +
                                   exam_start_class + ' and ' + exam_end_class)
                            print ('Exception = %s (%s)' % (e.message, type(e)))
                            error = 'unable to create exam ' + exam_title + ' with start date: ' \
                                    + str(exam_start_date) + ' and end date: ' + str(exam_end_date) + ' for ' + \
                                    exam_start_class + ' and ' + exam_end_class
                            form.errors['__all__'] = form.error_class([error])
                            print (error)
                            return render(request, 'classup/setup_data.html', context_dict)

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Exams Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


class ConfigurationList(generics.ListCreateAPIView):
    serializer_class = ConfigurationSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        q = Configurations.objects.filter(school=school)
        return q
