import os
import datetime
import xlrd
import json


from rest_framework import generics
from django.views.decorators.csrf import csrf_exempt

from django.contrib import messages
from django.contrib.auth.models import User, Group

from django.shortcuts import render
from setup.forms import ExcelFileUploadForm

from authentication.views import JSONResponse

from setup.models import School, UserSchoolMapping
from academics.models import Class, Section, Subject, TestResults, ClassTeacher, Exam, TeacherSubjects
from teacher.models import Teacher
from student.models import Student, Parent, DOB
from .models import Configurations

from .serializers import ConfigurationSerializer

from operations import sms

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


def check_reg_no(request):
    print('inside check_reg_no')
    response_dict = {

    }
    school_id = request.GET.get('school_id')
    the_class = request.GET.get('the_class')
    section = request.GET.get('section')
    roll_no = request.GET.get('roll_no')
    try:
        school = School.objects.get(id=school_id)
    except Exception as e:
        print ('Exception 210 from setup views.py = %s (%s)' % (e.message, type(e)))
        print ('unable to fetch the school for school with id:  ' + school_id)

    reg_no = request.GET.get('reg_no')
    try:
        student = Student.objects.get(school=school, student_erp_id=reg_no)
        name = student.fist_name + ' ' + student.last_name
        the_class = student.current_class.standard + ' ' + student.current_section.section
        error_message = 'Reg No ' + reg_no + ' is already associated with '
        error_message += name
        error_message += ' of class '
        error_message += the_class
        response_dict['status'] = 'error'
        response_dict['error_message'] = error_message
        print(error_message)
        return JSONResponse(response_dict, status=201)
    except Exception as e:
        print ('Exception 220 from setup views.py = %s (%s)' % (e.message, type(e)))
        print ('registrton number:  ' + reg_no + ' is available')

        # now check if roll number is supplied, it is not already allotted to another student
        if roll_no != '':
            try:
                c = Class.objects.get(school=school, standard=the_class)
                sec = Section.objects.get(school=school, section=section)
                student = Student.objects.get(school=school, current_class=c, current_section=sec, roll_number=roll_no)
                response_dict['status'] = 'error'
                error_message = 'Roll No ' + str(roll_no) + ' is already associated with '
                error_message += student.fist_name + ' ' + student.last_name
                response_dict['error_message'] = error_message
                print(error_message)
                return JSONResponse(response_dict, status=201)
            except Exception as e:
                print('Exception 310 from setup view.py = %s (%s)' % (e.message, type(e)))
                print('No conflict of registration number and roll number ')
                response_dict['status'] = 'success'
                return JSONResponse(response_dict, status=200)
    response_dict['status'] = 'success'
    return JSONResponse(response_dict, status=200)


@csrf_exempt
def delete_stuednt(request):
    context_dict =  {

    }
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data['student_id']
            student = Student.objects.get(id=student_id)
            student.active_status = False
            student.save()
            context_dict['status'] = 'success'
            return JSONResponse(context_dict, status=200)
        except Exception as e:
            error_message = 'Failed to set active_status of ' + student.fist_name + ' ' \
                            + student.last_name + ' to False'
            context_dict['status'] = 'failed'
            context_dict['error_message'] = error_message
            return JSONResponse(context_dict, status=201)


@csrf_exempt
def update_student(request):
    context_dict = {

    }
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)
            sender = data['user']
            school_id = data['school_id']
            school = School.objects.get(id=school_id)
            student_id = data['student_id']
            student_first_name = data['first_name']
            student_last_name = data['last_name']
            parent_name = data['parent_name']
            parent_mobile1 = data['mobile1']
            parent_mobile2 = data['mobile2']
            if parent_mobile2 == '':
                parent_mobile2 = '1234567890'
            current_class = data['the_class']
            current_section = data['section']
            current_roll_no = data['roll_no']
            parent_email = 'dummy@testmail.com'

            # check to see if the primary mobile of parent has been changed. If it is then we need to create a new
            # user for parent and send them sms
            try:
                p = Parent.objects.get(parent_mobile1=parent_mobile1)

                if p:
                    print ('Parent ' + parent_name + ' already exist. This will be updated!')
                    p.parent_name = parent_name
                    p.parent_mobile1 = parent_mobile1
                    p.parent_mobile2 = parent_mobile2
                    p.parent_email = parent_email
            except Exception as e:
                print ('Exception 350 from setup views.py = %s (%s)' % (e.message, type(e)))
                print ('Parent ' + parent_name + ' is a new entry. This will be created!')
                p = Parent(parent_name=parent_name, parent_mobile1=parent_mobile1,
                           parent_mobile2=parent_mobile2, parent_email=parent_email)
            try:
                p.save()
            except Exception as e:
                print ('Exception 360 from setup views.py = %s (%s)' % (e.message, type(e)))
                print('Unable to save the parent data for ' + parent_name + ' in Table Parent')

            # now, create a user for this parent (only if the primary mobile has changed)
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
                print ('Exception 370 from setup views.py = %s (%s)' % (e.message, type(e)))
                print ('Unable to create user for ' + parent_name)

            try:
                conf = Configurations.objects.get(school=school)
                if whether_new_user:
                    android_link = conf.google_play_link
                    iOS_link = conf.app_store_link

                    # send login id and password to parent via sms
                    message = 'Dear ' + parent_name + ', Welcome to ClassUp. '
                    message += 'Now you can track ' +  student_first_name +  "'s progress at " + school.school_name
                    message += '. Your user id is: ' + str(parent_mobile1) + ', and password is: '
                    message += str(password)
                    message += '. Please install ClassUp from these links. Android: '
                    message += android_link
                    message += '. iPhone/iOS: '
                    message += iOS_link
                    message += '. For support, email to: support@classup.in'
                    print(message)
                    message_type = 'Welcome Parent'
                    sms.send_sms1(school, sender, str(parent_mobile1), message, message_type)
            except Exception as e:
                print ('Exception 380 in setup view.py = %s (%s)' % (e.message, type(e)))
                print ('Failed to send welcome sms to ' + parent_name)

            # update the student
            student = Student.objects.get(id=student_id)
            student.parent = p
            student.fist_name = student_first_name
            student.last_name = student_last_name

            the_class = Class.objects.get(school=school, standard=current_class)
            student.current_class = the_class

            the_section = Section.objects.get(school=school, section=current_section)
            student.current_section= the_section

            student.roll_number = current_roll_no
            student.save()
            context_dict['status'] = 'success'
            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('Exception 390 in setup views.py = %s (%s)' % (e.message, type(e)))
            error_message = 'unable to update student ' + student_first_name + ' class: ' \
                            + current_class + ' ' + current_section
            print(error_message)
            context_dict['status'] = 'error'
            return JSONResponse(context_dict, status=201)


@csrf_exempt
def add_student(request):
    context_dict = {
    }

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)
            sender = data['user']
            school_id = data['school_id']
            school = School.objects.get(id=school_id)
            student_id = data['reg_no']
            student_first_name = data['first_name']
            student_last_name = data['last_name']
            parent_name = data['parent_name']
            parent_mobile1 = data['mobile1']
            parent_mobile2 = data['mobile2']
            if parent_mobile2 == '':
                parent_mobile2 = '1234567890'
            current_class = data['the_class']
            current_section = data['section']
            current_roll_no = data['roll_no']
            parent_email = 'dummy@testmail.com'

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
                print ('Exception 230 from setup views.py = %s (%s)' % (e.message, type(e)))
                print ('Parent ' + parent_name + ' is a new entry. This will be created!')
                p = Parent(parent_name=parent_name, parent_mobile1=parent_mobile1,
                           parent_mobile2=parent_mobile2, parent_email=parent_email)
            try:
                p.save()
            except Exception as e:
                print ('Exception 240 from setup views.py = %s (%s)' % (e.message, type(e)))
                print('Unable to save the parent data for ' + parent_name + ' in Table Parent')

            # now, create a user for this parent

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
                print ('Exception 250 from setup views.py = %s (%s)' % (e.message, type(e)))
                print ('Unable to create user for ' + parent_name)

            try:
                conf = Configurations.objects.get(school=school)
                if whether_new_user:
                    android_link = conf.google_play_link
                    iOS_link = conf.app_store_link

                    # send login id and password to parent via sms
                    message = 'Dear ' + parent_name + ', Welcome to ClassUp. '
                    message += "Now you can track your child's progress at " + school.school_name + '. '
                    message += 'Your user id is: ' + str(parent_mobile1) + ', and password is: '
                    message += str(password)
                    message += '. Please install ClassUp from these links. Android: '
                    message += android_link
                    message += '. iPhone/iOS: '
                    message += iOS_link

                    message += '. For support, email to: support@classup.in'
                    print(message)
                    message_type = 'Welcome Parent'

                    sms.send_sms1(school, sender, str(parent_mobile1), message, message_type)
            except Exception as e:
                print ('Exception 260 in setup view.py = %s (%s)' % (e.message, type(e)))
                print ('Failed to send welcome sms to ' + parent_name)

            # now, start creating the student. The parent created above will be the parent of this student.

            # class and section are foreign keys. Get hold of the relevant objects
            print ('Class = ' + current_class)

            the_class = Class.objects.get(school=school, standard=current_class)
            the_section = Section.objects.get(school=school, section=current_section)

            # create student
            try:
                # if roll no was provided by School Admin, use it.
                if current_roll_no != '':
                    s = Student(school=school, student_erp_id=student_id, fist_name=student_first_name,
                                last_name=student_last_name, current_class=the_class, current_section=the_section,
                                roll_number=current_roll_no, parent=p)
                    s.save()
                    print ('saving successful!')
                else:
                    try:
                        # we need to generate a roll no for this student. Should be the current count of student in this
                        # class plus 1
                        max_roll_no = Student.objects.filter(school=school, current_class=the_class,
                                                             current_section=
                                                             the_section).latest('roll_number').roll_number
                        if max_roll_no is not None:
                            current_roll_no = max_roll_no + 1
                    except Exception as e:
                        print ('Exception 320 from setup views.py = %s (%s)' % (e.message, type(e)))
                        print('looks like this is the first student in this class. Hence roll no would be 1')
                        current_roll_no = 1

                    s = Student(school=school, student_erp_id=student_id, fist_name=student_first_name,
                                    last_name=student_last_name, current_class=the_class, current_section=the_section,
                                    roll_number=current_roll_no, parent=p)
                    s.save()
                print ('saving successful!')

                # this student should appear in all the pending test for this class & section
                # print ('creating an entry for this student in all pending test for this class/section')
                # try:
                #     tests = ClassTest.objects.filter(the_class=the_class, section=the_section, is_completed=False)
                #     for t in tests:
                #         test_result = TestResults(class_test=t, roll_no=current_roll_no,
                #                                           student=s, marks_obtained=-5000.00, grade='')
                #         try:
                #             test_result.save()
                #             print (' test results successfully created')
                #         except Exception as e:
                #             print ('failed to create test results')
                #             print ('Exception 270 from setup views.py = %s (%s)' % (e.message, type(e)))
                # except Exception as e:
                #     print ('Currently no pending tests for this class/section')
                #     print ('Exception 280 from setup views.py = %s (%s)' % (e.message, type(e)))
            except Exception as e:
                error = 'Unable to create the new student in the database'
                print (error)
                print ('Exception 290 from setup views.py = %s (%s)' % (e.message, type(e)))
        except Exception as e:
            print ('Exception 300 in setup view.py = %s (%s)' % (e.message, type(e)))
            print ('Failed to add student ' + student_first_name + ' ' + student_last_name +
                   ' to ' + current_class + ' ' + current_section)
    return JSONResponse(context_dict, status=200)


@csrf_exempt
def setup_students(request):
    context_dict = {}

    context_dict['user_type'] = 'school_admin'
    context_dict['school_name'] = request.session['school_name']

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
                print ('now starting to process the uploaded file for setting up Student data for school ' +
                       school.school_name)
                file_to_process_handle = request.FILES['excelFile']
                conf = Configurations.objects.get(school=school)

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
                    col = 1
                    student_id = str(sheet.cell(row, col).value)
                    print('student id =',  student_id)
                    col += 1

                    # sometimes names are in lowercase. We need to convert the first letter to uppercase
                    student_first_name_raw = sheet.cell(row, col).value
                    print ('first name = %s'% student_first_name_raw)
                    student_first_name = student_first_name_raw.title()
                    col += 1

                    student_last_name_raw = sheet.cell(row, col).value
                    print('last name = %s'% student_last_name_raw)
                    student_last_name = student_last_name_raw.title()
                    col += 1

                    current_class = sheet.cell(row, col).value
                    print('current class = ', current_class)
                    col += 1
                    current_section = sheet.cell(row, col).value
                    print('current section = ', current_section)
                    col += 1
                    current_roll_no_raw = sheet.cell(row, col).value
                    # 29/03/2018 - We are making roll no optional
                    if current_roll_no_raw == '':
                        print('roll number for %s has not been specified' % student_first_name)
                        current_roll_no_raw = 50
                        current_roll_no = int(current_roll_no_raw)
                    else:
                        # excel may add a decimal to the roll number. We need to convert it to integer
                        current_roll_no = int(current_roll_no_raw)
                        print('roll no = ', current_roll_no)
                        print (current_roll_no_raw)
                        print (current_roll_no)
                    col += 1

                    # now, capture the parent data
                    parent_name_raw = sheet.cell(row, col).value
                    print('parent name = ', parent_name_raw)
                    parent_name = parent_name_raw.title()
                    col += 1

                    # 24/11/2016 - as of now we will not be using email. Hence use dummy
                    # parent_email = sheet.cell(row, 7).value
                    parent_email = 'dummy@testmail.com'
                    col += 1

                    # we need to explicitly cast mobile number to string. Else update will not function properly
                    parent_mobile1_raw = sheet.cell(row, col).value
                    print('mobile 1 = ', parent_mobile1_raw)
                    print parent_mobile1_raw
                    col += 1
                    parent_mobile2_raw = sheet.cell(row, col).value
                    print('mobile 2= ', parent_mobile2_raw )
                    print parent_mobile2_raw

                    # excel can put a decimal followed by zero in mobile numbers. This needs to be fixed
                    parent_mobile1 = int(parent_mobile1_raw)
                    print parent_mobile1

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
                        print ('Exception2 from setup views.py = %s (%s)' % (e.message, type(e)))
                        print ('Parent ' + parent_name + ' is a new entry. This will be created!')
                        p = Parent(parent_name=parent_name, parent_mobile1=parent_mobile1,
                                   parent_mobile2=parent_mobile2, parent_email=parent_email)
                    try:
                        p.save()
                    except Exception as e:
                        print ('Exception 18122018-A from setup views.py = %s (%s)' % (e.message, type(e)))
                        error = 'Unable to save the parent data for ' + parent_name + ' in Table Parent'
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        continue
                    # now, create a user for this parent

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
                        print ('Exception4 from setup views.py = %s (%s)' % (e.message, type(e)))
                        print ('Unable to create user for ' + parent_name)
                        # todo implement the code to send password to the user through an sms and email

                    try:
                        if whether_new_user:
                            android_link = conf.google_play_link
                            iOS_link = conf.app_store_link

                            # send login id and password to parent via sms
                            message = 'Dear ' + parent_name + ', Welcome to ClassUp. '
                            message += "Now you can track your child's progress at " + school.school_name + '. '
                            message += 'Your user id is: ' + str(parent_mobile1) + ', and password is: '
                            message += str(password)
                            # message += 'using ClassUp App. '
                            message += '. Please install ClassUp from these links. Android: '
                            message += android_link
                            message += '. iPhone/iOS: '
                            message += iOS_link

                            # message += '. You can change your password after first login. '
                            message += '. For support, email to: support@classup.in'
                            print(message)
                            message_type = 'Welcome Parent'
                            sender = request.session['user']

                            sms.send_sms1(school, sender, str(parent_mobile1), message, message_type)
                    except Exception as e:
                        print ('Exception1 in setup view.py = %s (%s)' % (e.message, type(e)))
                        print ('Failed to send welcome sms to ' + parent_name)

                    # now, start creating the student. The parent created above will be the parent of this student.

                    # class and section are foreign keys. Get hold of the relevant objects
                    print ('Class = ' + current_class)

                    try:
                        the_class = Class.objects.get(school=school, standard=current_class)
                    except Exception as e:
                        error = 'Unable to retrieve the relevant class: ' + current_class
                        print ('Exception5 from setup views.py = %s (%s)' % (e.message, type(e)))
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        # todo - we should skip this student but report this and move on to the next student <provide code>
                        continue

                    try:
                        the_section = Section.objects.get(school=school, section=current_section)
                    except Exception as e:
                        print ('Exception 6 from setup views.py = %s (%s)' % (e.message, type(e)))
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

                            # 25/07/2017 - it might be possible that the student was deleted (de-activated) earlier
                            s.active_status = True
                    except Exception as e:
                        print ('Exception7 from setup views.py = %s (%s)' % (e.message, type(e)))
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
                            # print ('creating an entry for this student in all pending test for this class/section')
                            # try:
                            #     tests = ClassTest.objects.filter(the_class=the_class,
                            #                                      section=the_section, is_completed=False)
                            #     for t in tests:
                            #         test_result = TestResults(class_test=t, roll_no=current_roll_no,
                            #                                   student=s, marks_obtained=-5000.00, grade='')
                            #         try:
                            #             test_result.save()
                            #             print (' test results successfully created')
                            #         except Exception as e:
                            #             print ('failed to create test results')
                            #             print ('Exception8 from setup views.py = %s (%s)' % (e.message, type(e)))
                            # except Exception as e:
                            #     print ('Currently no pending tests for this class/section')
                            #     print ('Exception9 from setup views.py = %s (%s)' % (e.message, type(e)))
                        except Exception as e:
                            error = 'Unable to create the new student in the database'
                            print (error)
                            print ('Exception10 from setup views.py = %s (%s)' % (e.message, type(e)))
                            form.errors['__all__'] = form.error_class([error])
                            # todo - we should skip this student but report this and move on to the next student <provide code>
                    try:
                        s.save()
                        print ('updated Student with  ID: ' + student_id + ' & name: ' + student_first_name)

                        # 04/01/2016 - if the roll number has been changed, we need to update the marks entry list
                        if update_marks_list:
                            print ('going to update the roll number in Class Test Results')
                            try:
                                results = TestResults.objects.filter(student=s, class_test__is_completed=False)
                                for r in results:
                                    r.roll_no = current_roll_no
                                    try:
                                        r.save()
                                        print ('roll number updated in test_result')
                                    except Exception as e:
                                        print ('unable to change roll number in test result')
                                        print ('Exception11 from setup views.py = %s (%s)' % (e.message, type(e)))
                            except Exception as e:
                                print ('no pending tests for which roll number needs to be changed')
                                print ('Exception 12 from setup views.py= %s (%s)' % (e.message, type(e)))
                            update_marks_list = False
                    except Exception as e:
                        print ('Exception13 from setup views.py = %s (%s)' % (e.message, type(e)))
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
                print ('Exception14 from setup views.py = %s (%s)' % (e.message, type(e)))
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
    context_dict['school_name'] = request.session['school_name']

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
                        print('Exception15 from setup views.py = %s (%s)' % (e.message, type(e)))
                        print('class ' + class_standard + ' is a new class. Hence inserting...')
                        try:
                            c = Class(standard=class_standard)
                            c.school = school
                            c.sequence = class_sequence
                            c.save()
                        except Exception as e:
                            print ('Exception16 from setup views.py = %s (%s)' % (e.message, type(e)))
                            error = 'Unable to save the class ' + class_standard + ' in table Class'
                            form.errors['__all__'] = form.error_class([error])
                            print(error)
                            return render(request, 'classup/setup_data.html', context_dict)

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Classes Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print('Exception17 from setup views.py = %s (%s)' % (e.message, type(e)))
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
    context_dict['school_name'] = request.session['school_name']

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
                            print ('Section ' + section + ' for school ' + school.school_name
                                   + ' already exist. Hence skipping...')
                    except Exception as e:
                        print ('Exception18 from setup views.py = %s (%s)' % (e.message, type(e)))
                        print ('Section ' + section + ' is a new section. Hence inserting...')
                        try:
                            s = Section(section=section)
                            s.school = school
                            s.save()
                        except Exception as e:
                            print ('Exception19 from setup views.py = %s (%s)' % (e.message, type(e)))
                            error = 'Unable to save the data in Table Section'
                            form.errors['__all__'] = form.error_class([error])
                            print (error)
                            return render(request, 'classup/setup_data.html', context_dict)
                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Section Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception20 from setup views.py = %s (%s)' % (e.message, type(e)))
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
    context_dict['school_name'] = request.session['school_name']

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
                        print ('Exception21 from setup views.py = %s (%s)' % (e.message, type(e)))
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
                            except Exception as e:
                                print ('Exception 22B from setup views.py = %s (%s)' % (e.message, type(e)))
                                print ('Unable to create user  ' + f_name + ' ' + l_name)
                            try:
                                mapping = UserSchoolMapping(user=user, school=school)
                                mapping.save()
                            except Exception as e:
                                print ('Exception 22A from setup views.py = %s (%s)' % (e.message, type(e)))
                                print ('Unable to create user or user-school mapping for ' + f_name + ' ' + l_name)
                            # todo implement the code to send password to the user through an sms and email

                            # make this user part of the Teachers group
                            try:
                                group = Group.objects.get(name='teachers')
                                user.groups.add(group)
                                print ('Successfully added ' + f_name + ' ' + l_name + ' to the Teachers group')
                            except Exception as e:
                                print ('Exception22 from setup views.py = %s (%s)' % (e.message, type(e)))
                                print ('Unable to add ' + f_name + ' ' + l_name + ' to the Teachers group')

                            # get the links of app on Google Play and Apple App store
                            configuration = Configurations.objects.get(school=school)
                            android_link = configuration.google_play_link
                            iOS_link = configuration.app_store_link

                            # send login id and password to teacher via sms
                            message = 'Dear ' + f_name + ' ' + l_name + ', Welcome to ClassUp.'
                            message += ' Your user id is: ' + email + ', and password is: ' + password + '. '
                            message += 'Please install ClassUp from these links. Android: '
                            message += android_link
                            message += ', iPhone/iOS: '
                            message += iOS_link

                            message += 'You can change your password after first login. '
                            message += 'Enjoy managing your class with ClassUp!'
                            message += ' For support, email to: support@classup.in'
                            message_type = 'Welcome Teacher'
                            sender = request.session['user']

                            sms.send_sms1(school, sender, str(mobile), message, message_type)

                            # 15/07/2017 - Set up Main as default subject for this teacher
                            try:
                                print ('now trying to set teacher subject')
                                s = Subject.objects.get(school=school, subject_name='Main')
                            except Exception as e:
                                print('unable to retrieve Main subject as default for ')
                                print ('Exception 100 from setup views.py = %s (%s)' % (e.message, type(e)))

                            try:
                                ts = TeacherSubjects.objects.get(teacher=t, subject=s)
                                if ts:
                                    print('subject ' + s.subject_name + ' has already been selected by teacher '
                                          + t.first_name + ' ' + t.last_name)
                                    pass

                            except Exception as e:
                                print(
                                'now setting subject ' + s.subject_name + ' for teacher ' +
                                t.first_name + ' ' + t.last_name)
                                ts = TeacherSubjects(teacher=t, subject=s)
                                try:
                                    ts.save()
                                    print('successfully set subject ' + s.subject_name +
                                          ' for teacher ' + t.first_name + ' ' + t.last_name)
                                except Exception as e:
                                    print('unable to set subject ' + s.subject_name +
                                          ' for teacher ' + t.first_name + ' ' + t.last_name)
                                    print ('Exception 101 from setup views.py = %s (%s)' % (e.message, type(e)))

                        except Exception as e:
                            print ('Exception23 from setup views.py = %s (%s)' % (e.message, type(e)))
                            error = 'Unable to save the data for ' + f_name + ' ' + l_name + ' in Table Teacher'
                            form.errors['__all__'] = form.error_class([error])
                            print (error)
                            # todo - we should skip this teacher but report this and move on to the next treacher <provide code>
                            continue

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Teacher Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception24 from setup views.py = %s (%s)' % (e.message, type(e)))
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
    context_dict['school_name'] = request.session['school_name']

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
                        print ('Exception25 from setup views.py = %s (%s)' % (e.message, type(e)))
                        print ('Subject ' + sub_name + ' is a new entry. Hence inserting...')
                        s = Subject(school=school, subject_name=sub_name,
                                    subject_code=sub_code, subject_sequence=sub_sequence)
                    try:
                        s.save()
                    except Exception as e:
                        print ('Exception26 from setup views.py = %s (%s)' % (e.message, type(e)))
                        error = 'Unable to save the data for ' + sub_name + ' ' + sub_code + ' in Table Subject'
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Subjects Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception27 from setup views.py = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_class_teacher(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    context_dict['school_name'] = request.session['school_name']

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
                                print ('Exception28 from setup views.py = %s (%s)' % (e.message, type(e)))
                    except Exception as e:
                        print ('Exception29 from setup views.py = %s (%s)' % (e.message, type(e)))
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
                            print ('Exception30 from setup views.py = %s (%s)' % (e.message, type(e)))
                            error = ('unable to set class teacher ' + the_class + '-' + section)
                            form.errors['__all__'] = form.error_class([error])
                            print (error)
                            return render(request, 'classup/setup_data.html', context_dict)

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Class Teachers Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception31 from setup views.py = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_dob(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    context_dict['school_name'] = request.session['school_name']

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Date of Births of Students'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for setting up DOB...')
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
                    erp_id = sheet.cell(row, 0).value
                    print(erp_id)
                    try:
                        student = Student.objects.get(school=school, student_erp_id=erp_id)
                        print ('now dealing with %s %s' % (student.fist_name, student.last_name))
                    except Exception as e:
                        print ('student with erp id %s does not exist' % erp_id)
                        print ('exception 231017-G from setup views.py %s %s ' % (e.message, type(e)))
                        continue

                    dob = sheet.cell(row, 2).value
                    try:
                        date_of_birth = datetime.datetime(*xlrd.xldate_as_tuple(dob, fileToProcess.datemode))
                        print ('date of birth is in acceptable format')
                        print (date_of_birth)
                    except Exception as e:
                        print ('problem with date of birth for %s %s' % (student.fist_name, student.last_name))
                        print ('exception 231017-H from setup views.py %s %s ' % (e.message, type(e)))
                        continue

                    # get the student associated with this erp_id

                    try:
                        record = DOB.objects.get(student=student)
                        print ('date of birth for ' + student.fist_name + ' ' +
                               student.last_name + ' already exists. This will be updated')
                        try:
                            record.dob = date_of_birth
                            record.save()
                            print ('successfully updated the date of birth for ' +
                                   student.fist_name, ' ' + student.last_name)
                        except Exception as e:
                            print ('failed to update the date of birth for '+
                                   student.fist_name, ' ' + student.last_name)
                            print ('(exception 231017-A from setup views.py %s %s) ' % (e.message, type(e)))
                    except Exception as e:
                        print ('(exception 231017-B from setup views.py %s %s) ' % (e.message, type(e)))
                        print ('date of birth for ' + student.fist_name + ' ' +
                               student.last_name + ' is not in record. This will be created')
                        try:
                            new_record = DOB(student=student, dob=date_of_birth)
                            new_record.save()
                            print (('created date of birth entry for %s %s)' %
                                    (student.fist_name, student.last_name)))
                        except Exception as e:
                            print ('failed to create date of birth entry for %s %s)' %
                                   (student.fist_name, student.last_name))
                            print ('(exception 231017-C from setup views.py %s %s) ' % (e.message, type(e)))

                            # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Date of Births Uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 231017-E from setup views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_exam(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    context_dict['school_name'] = request.session['school_name']

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
                    exam_type = sheet.cell(row, 5).value


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
                            e.exam_type = exam_type
                            try:
                                e.save()
                                print ('successfully updated Exam ' + exam_title)
                            except Exception as e:
                                print ('unable to the update Exam ' + exam_title)
                                print ('Exception32 from setup views.py = %s (%s)' % (e.message, type(e)))

                    except Exception as e:
                        print ('Exception33 from setup views.py = %s (%s)' % (e.message, type(e)))
                        print ('Exam  ' + exam_title + ' for ' + exam_start_class + ' and ' +
                               exam_end_class + ' is not yet set. Setting it now...')
                        try:
                            e = Exam(school=school, title=exam_title, start_date=exam_start_date,
                                      end_date=exam_end_date, start_class=exam_start_class, end_class=exam_end_class,
                                      exam_type=exam_type)
                            e.save()
                            print ('successfully created Exam  ' + exam_title + ' with start date: '
                                   + str(exam_start_date) + ' and end date: ' + str(exam_end_date) +
                                   ' for ' + exam_start_class + ' and ' + exam_end_class)
                        except Exception as e:
                            print ('unable to create exam ' + exam_title + ' with start date: '
                                   + str(exam_start_date) + ' and end date: ' + str(exam_end_date) + ' for ' +
                                   exam_start_class + ' and ' + exam_end_class)
                            print ('Exception34 from setup views.py = %s (%s)' % (e.message, type(e)))
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
                print ('Exception35 from setup views.py = %s (%s)' % (e.message, type(e)))
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
