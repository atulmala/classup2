import StringIO
import json
from datetime import date

import xlsxwriter
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.models import User, Group

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from formats.formats import Formats as format
from operations import sms
from authentication.views import log_entry
from academics.models import Subject, ClassTeacher, Class, Section, TeacherSubjects
from setup.models import School, UserSchoolMapping, Configurations
from operations.models import SMSRecord
from student.models import Student
from .models import Teacher, TeacherAttendance, TeacherAttendnceTaken, TeacherMessageRecord, MessageReceivers

from operations.serializers import SMSDetailSerializer

from .serializers import TeacherSubjectSerializer, TeacherSerializer, \
    TeacherAttendanceSerializer, TeacherMessageRecordSerializer, MessageReceiversSerializer

from authentication.views import JSONResponse


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class TeacherMessageList (generics.ListAPIView):
    serializer_class = TeacherMessageRecordSerializer

    def get_queryset(self):
        t = self.kwargs['teacher']
        the_teacher = Teacher.objects.get(email=t)

        q = TeacherMessageRecord.objects.filter(teacher=the_teacher).order_by ('-date')

        return q


class CircularList(generics.ListAPIView):
    serializer_class = SMSDetailSerializer

    def get_queryset(self):
        teacher_email = self.kwargs['teacher']
        sender_type = self.kwargs['sender_type']
        teacher = Teacher.objects.get(email=teacher_email)
        mobile = teacher.mobile

        print('getting the list of SMS received by %s %s' % (teacher.first_name, teacher.last_name))
        q = SMSRecord.objects.filter(recipient_number=mobile, sender_type=sender_type).order_by('-date')
        return q


class MessageReceiversList (generics.ListAPIView):
    serializer_class = MessageReceiversSerializer

    def get_queryset(self):
        key = self.kwargs['key']
        teacher_record = TeacherMessageRecord.objects.get (id=key)

        q = MessageReceivers.objects.filter (teacher_record=teacher_record)
        return q


class TeacherSubjectList(generics.ListCreateAPIView):
    serializer_class = TeacherSubjectSerializer

    def get_queryset(self):
        t = self.kwargs['teacher']

        the_teacher = Teacher.objects.get(email=t)

        q = TeacherSubjects.objects.filter(teacher=the_teacher).order_by('subject__subject_sequence')

        return q


class TeacherList(generics.ListAPIView):
    serializer_class = TeacherSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)

        q = Teacher.objects.filter(school=school, active_status=True).order_by('first_name')
        return q


class TheTeacherAttendance(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = TeacherAttendanceSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        d = self.kwargs['d']
        m = self.kwargs['m']
        y = self.kwargs['y']

        q1 = TeacherAttendance.objects.filter(school=school, date=date(int(y), int(m), int(d)))
        return q1

    def post(self, request, *args, **kwargs):
        print('starting to process teacher Attendance')
        print('request=')
        print(request.body)
        data = json.loads(request.body)
        print ('json=')
        print (data)
        for key in data:
            print (key)

        school_id = self.kwargs['school_id']
        print(school_id)
        school = School.objects.get(pk=school_id)
        print (school)

        d = self.kwargs['d']
        m = self.kwargs['m']
        y = self.kwargs['y']
        the_date = date(int(y), int(m), int(d))
        print (the_date)

        # record the attendance taken
        try:
            q = TeacherAttendnceTaken.objects.filter(school=school, date=the_date)
            if 0 == q.count():
                a = TeacherAttendnceTaken(school=school, date=the_date)
                a.save()
        except Exception as e:
            print ('failed to create Teacher Attendance Taken record')
            print ('Exception 111117-A from teacher views.py %s %s' % (e.message, type(e)))

        # process the corrections
        print (data['corrections'])
        print ('correction list: ')
        for correction_id in data['corrections']:
            print (correction_id)
            try:
                teacher = Teacher.objects.get(id=correction_id)
                record = TeacherAttendance.objects.get(teacher=teacher, date=the_date)
                record.delete()
                print ('deleted previously recorded attendance for %s %s' % (teacher.first_name, teacher.last_name))
            except Exception as e:
                print ('unable to delete a previously marked attenance for %s %s' %
                       (teacher.first_name, teacher.last_name))
                print ('Exception 111117-B from teacher views.py %s %s' % (e.message, type(e)))

        print (data['absentees'])
        print ('absentees list: ')
        for absentee_id in data['absentees']:
            print (absentee_id)
            try:
                teacher = Teacher.objects.get(id=absentee_id)
                record = TeacherAttendance.objects.filter(teacher=teacher, date=the_date)
                if not record:
                    record = TeacherAttendance(teacher=teacher, date=the_date)
                    record.save()
                    print ('marked absence for %s %s ' % (teacher.first_name, teacher.last_name))
                else:
                    print ('absence for %s %s was already marked in a previous attendance' %
                           (teacher.first_name, teacher.last_name))
            except Exception as e:
                print ('failed to mark for %s %s ' % (teacher.first_name, teacher.last_name))
                print ('Exception 111117-C from teacher views.py %s %s' % (e.message, type(e)))

        return Response(status=status.HTTP_200_OK)


class TheTeacherAttendance1(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    serializer_class = TeacherAttendanceSerializer

    def get(self, request, *args, **kwargs):
        print ('from class based view')

        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Arrangement'

        school_id = request.session['school_id']
        context_dict['school_id'] = school_id
        print ('school_id = %i' % school_id)
        try:
            school = School.objects.get(id=school_id)
            print ('school= %s' % school.school_name)
            teacher_list = Teacher.objects.filter (school=school).order_by ('first_name')
            context_dict['teacher_list'] = teacher_list
            today = date.today()
            absentees = TeacherAttendance.objects.filter (school=school, date__year=today.year,
                                                            date__month=today.month, date__day=today.day)
            absent_list = []
            for a in absentees:
                absent_list.append(a.teacher.id)
            print('abent_list = ')
            print(absent_list)

            context_dict['absent_list'] = absent_list
        except Exception as e:
            print ('exception 21122017-A from teachers views.py %s %s' % (e.message, type(e)))
        return render(request, 'classup/teacher_attendance.html', context_dict)

    def post(self, request, *args, **kwargs):
        print('starting to process teacher Attendance submitted from web portal')
        print('request=')
        print(request.body)
        try:
            data = json.loads(request.body)
            print ('json=')
            print (data)
        except Exception as e:
            print ('failed to load json from request')
            print ('Exception 23122017-B from teacher views.py %s %s' % (e.message, type(e)))

        school_id = self.kwargs['school_id']
        print(school_id)
        school = School.objects.get(pk=school_id)
        print (school)

        # record the attendance taken
        try:
            q = TeacherAttendnceTaken.objects.filter(school=school, date=date.today())
            if 0 == q.count():
                a = TeacherAttendnceTaken(school=school, date=date.today())
                a.save()
            else:
                try:
                    TeacherAttendance.objects.filter(school=school, date=date.today()).delete()
                except Exception as e:
                    print ('failed to delete Teacher attendance for today')
                    print ('Exception 23122017-A from techer view.py %s %s' % (e.message, type(e)))
        except Exception as e:
            print ('failed to create Teacher Attendance Taken record')
            print ('Exception 111117-A from teacher views.py %s %s' % (e.message, type(e)))

        for key in data:
            absentee_id = data[key]
            print (absentee_id)
            try:
                teacher = Teacher.objects.get(id=absentee_id)
                record = TeacherAttendance.objects.filter(teacher=teacher, date=date.today())
                if not record:
                    record = TeacherAttendance(teacher=teacher, date=date.today())
                    record.save()
                    print ('marked absence for %s %s ' % (teacher.first_name, teacher.last_name))
                else:
                    print ('absence for %s %s was already marked in a previous attendance' %
                           (teacher.first_name, teacher.last_name))
            except Exception as e:
                print ('failed to mark for %s %s ' % (teacher.first_name, teacher.last_name))
                print ('Exception 111117-C from teacher views.py %s %s' % (e.message, type(e)))

        return Response(status=status.HTTP_200_OK)


def whether_class_teacher(request, teacher_id):
    response_dict = {

    }

    if request.method == 'GET':
        try:
            t = Teacher.objects.get(id=teacher_id)
            response_dict['status'] = 'success'
            if ClassTeacher.objects.filter(class_teacher=t).first():
                ct = ClassTeacher.objects.filter(class_teacher=t)[0]
                response_dict['is_class_teacher'] = 'true'
                response_dict['the_class'] = ct.standard.standard
                response_dict['section'] = ct.section.section
            else:
                response_dict['is_class_teacher'] = 'false'
        except Exception as e:
            print('Exception 70 from teachers views.py %s %s' % (e.message, type(e)))
            response_dict['status'] = 'failure'

    return JSONResponse(response_dict, status=200)


def whether_class_teacher2(request, teacher):
    response_dict = {

    }

    if request.method == 'GET':
        try:
            t = Teacher.objects.get(email=teacher)
            response_dict['status'] = 'success'
            if ClassTeacher.objects.filter(class_teacher=t).first():
                ct = ClassTeacher.objects.filter(class_teacher=t)[0]
                response_dict['is_class_teacher'] = 'true'
                response_dict['the_class'] = ct.standard.standard
                response_dict['section'] = ct.section.section
            else:
                response_dict['is_class_teacher'] = 'false'
        except Exception as e:
            print('Exception 70 from teachers views.py %s %s' % (e.message, type(e)))
            response_dict['status'] = 'failure'

    return JSONResponse(response_dict, status=200)


@csrf_exempt
def delete_teacher(request):
    response_dict = {

    }

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            teacher_id = data['teacher_id']
            teacher = Teacher.objects.get(id=teacher_id)
            teacher.active_status = False
            teacher.save()
            response_dict['status'] = 'success'
            return JSONResponse(response_dict, status=200)
        except Exception as e:
            print('Exception 80 from teachers views.py = %s (%s) ' % (e.message, type(e)))
            error_message = 'Failed to set active_status of ' + teacher.first_name + ' ' \
                            + teacher.last_name + ' to False'
            teacher['status'] = 'failed'
            teacher['error_message'] = error_message
            return JSONResponse(response_dict, status=201)


class ClassTeacherList(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        school_id = data['school_id']
        school = School.objects.get(id=school_id)

        file_name = 'class_teacher.xlsx'
        output = StringIO.StringIO(file_name)
        file = xlsxwriter.Workbook(output)
        fmt = format()
        title_format = file.add_format(fmt.get_title())
        title_format.set_border()
        header = file.add_format(fmt.get_header())
        cell_bold = file.add_format(fmt.get_cell_bold())
        cell_bold.set_border()
        cell_center = file.add_format(fmt.get_cell_center())
        cell_center.set_border()
        cell_left = file.add_format(fmt.get_cell_left())
        cell_left.set_border()
        cell_normal = file.add_format(fmt.get_cell_normal())
        cell_normal.set_border()
        sheet_name = 'Class Teacher List'
        sheet = file.add_worksheet(sheet_name)
        sheet.set_portrait()
        sheet.set_paper(9)
        sheet.fit_to_pages(1, 0)
        sheet.set_footer('&L%s&R%s' % (school.school_name, 'Class Teacher List'))
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 8)
        sheet.set_column('C:C', 8)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 15)

        sheet.merge_range('A1:E1', school.school_name, header)
        sheet.merge_range('A2:E2', 'Class Teacher List', header)

        row = 2
        col = 0
        s_no = 1
        sheet.write_string(row, col, 'S No', cell_bold)
        col += 1
        sheet.write_string(row, col, 'Class', cell_bold)
        col += 1
        sheet.write_string(row, col, 'Section', cell_bold)
        col += 1
        sheet.write_string(row, col, 'Class Teacher', cell_bold)
        col += 1
        sheet.write_string(row, col, 'Mobile Number', cell_bold)
        row += 1
        col = 0

        classes = Class.objects.filter(school=school).order_by('sequence')
        sections = Section.objects.filter(school=school).order_by('section')

        for a_class in classes:
            for section in sections:
                students = Student.objects.filter(current_class=a_class, current_section=section)
                if students.count() < 1:
                    print('class %s-%s of %s is empty. skipping...' % (a_class, section, school))
                    continue
                print('determining the class teacher for class %s-%s in %s' % (a_class, section, school))
                sheet.write_number(row, col, s_no, cell_normal)
                s_no += 1
                col += 1
                sheet.write_string(row, col, a_class.standard, cell_normal)
                col += 1
                sheet.write_string(row, col, section.section, cell_normal)
                col += 1

                try:
                    ct = ClassTeacher.objects.get(school=school, standard=a_class, section=section)
                    class_teacher = ct.class_teacher
                    name = '%s %s' % (class_teacher.first_name, class_teacher.last_name)
                    sheet.write_string(row, col, name, cell_left)
                    col += 1

                    mobile = class_teacher.mobile
                    sheet.write_string(row, col, mobile, cell_normal)
                except Exception as e:
                    print('exception 04022020-D from teacher views.py %s %s' % (e.message, type(e)))
                    print('class teacher for class %s-%s of %s not set' % (a_class, section, school))
                    sheet.write_string(row, col, 'Not Set', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'Not Set', cell_bold)
                row += 1
                col = 0
        file.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s' % file_name
        response.write(output.getvalue())
        return response


class SetClassTeacher(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        school_id = data['school_id']
        school = School.objects.get(id=school_id)
        the_class = data['the_class']
        c = Class.objects.get(school=school, standard=the_class)
        section = data['section']
        s = Section.objects.get(school=school, section=section)
        teacher_id = data['teacher_id']
        t = Teacher.objects.get(id=teacher_id)

        try:
            ct = ClassTeacher.objects.get(school=school, standard=c, section=s)
            cct = ct.class_teacher  # current class teacher?
            ct.class_teacher = t
            ct.save()
            message = cct.first_name + ' ' + cct.last_name + ' was the Class Teacher for class '
            message += the_class + ' ' + section + '. Now the new Class Teacher is '
            message += '%s %s' % (t.first_name, t.last_name)
            print(message)
            response_dict = {'message': message}
            response_dict['status'] = 'success'
            return JSONResponse(response_dict, status=200)
        except Exception as e:
            print('Exception 04022020-A from teachers views.py = %s (%s) ' % (e.message, type(e)))
            print('no Class Teacher was set for class ' + the_class + ' ' + section + '. Setting now...')
            try:
                ct = ClassTeacher()
                ct.school = school
                ct.standard = c
                ct.section = s
                ct.class_teacher = t
                ct.save()
                message = '%s is now assigned as Class Teacher for class ' % t
                message += the_class + ' ' + section
                print(message)
                response_dict['message'] = message
                response_dict['status'] = 'success'
                return JSONResponse(response_dict, status=200)
            except Exception as e:
                print ('Exception 04022020-B from teachers views.py = %s (%s) ' % (e.message, type(e)))
                error_message = 'failed to set %s as Class Teacher for class: ' % t
                error_message += the_class + ' ' + section
                print(error_message)
                response_dict['error_message'] = error_message
                return JSONResponse(response_dict, status=201)


@csrf_exempt
def update_teacher(request):
    response_dict = {

    }
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)
            teacher_id = data['teacher_id']
            teacher_login = data['teacher_login']
            teacher_mobile = data['teacher_mobile']
            teacher_name = data['teacher_name']
            first_name = teacher_name.split()[0]
            last_name = ' '
            try:
                last_name += teacher_name.split()[1]
                last_name += ' %s' % teacher_name.split()[2]
            except Exception as e:
                print('exception 03022020-B from teacher views.py %s %s' % (e.message, type(e)))
                print('last name of teacher not mentioned completely')

            teacher = Teacher.objects.get(id=teacher_id)
            teacher.first_name = first_name
            teacher.last_name = last_name
            teacher.email = teacher_login
            teacher.mobile = teacher_mobile
            teacher.save()

            message = 'Teacher ' + teacher_name + ' updated. '
            print (message)
            response_dict['status'] = 'success'
            response_dict['message'] = message

            if data['is_class_teacher'] == 'true':
                print('starting to set this teacher as Class Teacher...')
                school_id = data['school_id']
                school = School.objects.get(id=school_id)
                the_class = data['the_class']
                c = Class.objects.get(school=school, standard=the_class)
                section = data['section']
                s = Section.objects.get(school=school, section=section)
                t = Teacher.objects.get(id=teacher_id)
                try:
                    ct = ClassTeacher.objects.get(school=school, standard=c, section=s)
                    cct = ct.class_teacher  # current class teacher?
                    ct.class_teacher = t
                    ct.save()
                    message += cct.first_name + ' ' + cct.last_name +  ' was the Class Teacher for class '
                    message += the_class + ' ' + section + '. Now the new Class Teacher is '
                    message += teacher_name
                    print(message)
                    response_dict['message'] = message
                    response_dict['status'] = 'success'
                    return JSONResponse(response_dict, status=200)
                except Exception as e:
                    print('Exception 90 from teachers views.py = %s (%s) ' % (e.message, type(e)))
                    print('no Class Teacher was set for class ' + the_class + ' ' + section + '. Setting now...')
                    try:
                        ct = ClassTeacher()
                        ct.school = school
                        ct.standard = c
                        ct.section = s
                        ct.class_teacher = t
                        ct.save()
                        message += teacher_name + ' is now assigned as Class Teacher for class '
                        message += the_class + ' ' + section
                        print(message)
                        response_dict['message'] = message
                        response_dict['status'] = 'success'
                        return JSONResponse(response_dict, status=200)
                    except Exception as e:
                        print ('Exception 100 from teachers views.py = %s (%s) ' % (e.message, type(e)))
                        error_message = 'failed to set ' + teacher_name + ' as Class Teacher for class: '
                        error_message +=  the_class + ' ' + section
                        print(error_message)
                        response_dict['error_message'] = error_message
                        return JSONResponse(response_dict, status=201)
            return JSONResponse(response_dict, status=200)
        except Exception as e:
            print ('Exception 110 from teachers views.py = %s (%s) ' % (e.message, type(e)))
            error_message = 'Failed to update teacher'
            print(error_message)
            response_dict['status'] = 'failure'
            response_dict['error_message'] = error_message
            return JSONResponse(response_dict, status=201)


@csrf_exempt
def add_teacher(request):
    print('adding teacher from device...')
    response_dict = {

    }
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)
            user = data['user']
            school_id = data['school_id']
            #employee_id = data['employee_id']
            email = data['email']
            mobile = data['mobile']
            full_name = data['full_name']
            first_name = full_name.split()[0]
            last_name = ' '
            try:
                last_name += full_name.split()[1]
                last_name += ' %s' % full_name.split()[2]
            except Exception as e:
                print('exception 03022020-A from teacher views.py %s %s' % (e.message, type(e)))
                print('last name of teacher not mentioned completely')

            school = School.objects.get(id=school_id)

            # check to see if any other teacher in this school has the same login id

            try:
                t = Teacher.objects.get(school=school, email=email)
                response_dict['status'] = 'failed'
                message = 'login id ' + email + ' is already assigned to ' + t.first_name + ' ' + t.last_name
                print(message)
                response_dict['message'] = message
                response_dict['status'] = 'failed'
                return JSONResponse(response_dict, status=201)
            except Exception as e:
                print('Exception 20 from teacher views.py = %s (%s) ' % (e.message, type(e)))
                print('login id are available. Hence this teacher can be added...')
                t = Teacher()
                t.school = school
                t.first_name = first_name
                t.last_name = last_name
                t.email = email
                t.mobile = mobile
                t.active_status = True
                try:
                    t.save()
                    # now, create a user for this teacher
                    # the user name would be the email, and password would be a random string
                    password = User.objects.make_random_password(length=5, allowed_chars='1234567890')

                    print ('Initial password = ' + password)
                    u = None
                    try:
                        u = User.objects.create_user(email, email, password)
                        u.first_name = first_name
                        u.last_name = last_name
                        u.is_staff = True
                        u.save()
                        print ('Successfully created user for ' + first_name + ' ' + last_name)

                        mapping = UserSchoolMapping(user=u, school=school)
                        mapping.save()
                    except Exception as e:
                        print ('Exception 50 from teacher views.py = %s (%s)' % (e.message, type(e)))
                        print ('Unable to create user or user-school mapping for ' + first_name + ' ' + last_name)

                    # make this user part of the Teachers group
                    try:
                        group = Group.objects.get(name='teachers')
                        u.groups.add(group)
                        print ('Successfully added ' + first_name + ' ' + last_name + ' to the Teachers group')
                    except Exception as e:
                        print ('Exception 60 from teacher views.py = %s (%s)' % (e.message, type(e)))
                        print ('Unable to add ' + first_name + ' ' + last_name + ' to the Teachers group')

                    # get the links of app on Google Play and Apple App store
                    configuration = Configurations.objects.get(school=school)
                    android_link = configuration.google_play_link
                    iOS_link = configuration.app_store_link

                    # send login id and password to teacher via sms
                    message = 'Dear ' + first_name + ' ' + last_name + ', Welcome to ClassUp.'
                    message += ' Your user id is: ' + email + ', and password is: ' + password + '. '
                    message += 'Please install ClassUp from these links. Android: '
                    message += android_link
                    message += ', iPhone/iOS: '
                    message += iOS_link

                    message += 'You can change your password after first login. '
                    message += 'Enjoy managing your class with ClassUp!'
                    message += ' For support, email to: support@classup.in'
                    message_type = 'Welcome Teacher'
                    sender = user

                    sms.send_sms1(school, sender, str(mobile), message, message_type)

                    # 15/07/2017 - Set up Main as default subject for this teacher
                    try:
                        print ('now trying to set teacher subject')
                        s = Subject.objects.get(school=school, subject_name='Main')
                    except Exception as e:
                        print('unable to retrieve Main subject as default for ')
                        print ('Exception 210 from teachers views.py = %s (%s)' % (e.message, type(e)))

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
                            print ('Exception 211 from teachers views.py = %s (%s)' % (e.message, type(e)))

                    response_dict['status'] = 'success'
                    response_dict['message'] = "Teacher created. Welcome SMS sent to the teacher' mobile"
                    return JSONResponse(response_dict, status=200)
                except Exception as e:
                    print('Exception 30 from teacher views.py = %s (%s)' % (e.message, type(e)))
                    message = 'Failed to create Teacher. Please contact ClassUp Support'
                    print(message)
                    response_dict['message'] = message
                    response_dict['status'] = 'failed'
                    return JSONResponse(response_dict, status=201)
        except Exception as e:
            print('Exception 40 from teachers views.py = %s (%s)' % (e.message, type(e)))
            message = 'Failed to create Teacher. Please contact ClassUp Support'
            response_dict['message'] = message
            response_dict['status'] = 'failed'
            print(message)
            return JSONResponse(response_dict, status=201)


@csrf_exempt
def set_subjects(request, teacher):
    print ('request.body(set_subjects)=')
    if request.method == 'POST':
        t = Teacher.objects.get(email=teacher)
        print (t)
        print ('request.body(set_subjects)=')
        print (request.body)
        school = t.school

        data = json.loads(request.body)
        print ('data(set_subjects)=')
        print (data)

        for key in data:
            print('key(set_subjects)=' + key)
            subject = data[key]
            print('subject(set_subjects)=' + subject)
            print ('now trying to extract subject(set_subjects)')
            try:
                s = Subject.objects.get(school=school, subject_code=subject)
            except Exception as e:
                    print('unable to retrieve subject(set_subjects)')
                    print ('Exception1 from teacher views.py = %s (%s)' % (e.message, type(e)))

            print ('now trying to set teacher subject')

            try:
                ts = TeacherSubjects.objects.get(teacher=t, subject=s)
                if ts:
                    print('subject ' + s.subject_name + ' has already been selected by teacher '
                          + t.first_name + ' ' + t.last_name)
                    pass

            except Exception as e:
                print('now setting subject ' + s.subject_name + ' for teacher ' + t.first_name + ' ' + t.last_name)
                ts = TeacherSubjects(teacher=t, subject=s)
                try:
                    ts.save()
                    print('successfully set subject ' + s.subject_name +
                          ' for teacher ' + t.first_name + ' ' + t.last_name)
                except Exception as e:
                    print('unable to set subject ' + s.subject_name +
                          ' for teacher ' + t.first_name + ' ' + t.last_name)
                    print ('Exception 2 from teacher views.py = %s (%s)' % (e.message, type(e)))
        try:
            action = 'Subjects Set'
            log_entry(teacher, action, 'Normal', True)
        except Exception as e:
            print('unable to create logbook entry')
            print ('Exception 500 from teachers views.py %s %s' % (e.message, type(e)))

    return HttpResponse('OK')


@csrf_exempt
def unset_subjects(request, teacher):
    print ('request.body(unset_subjects)=')
    if request.method == 'POST':
        t = Teacher.objects.get(email=teacher)
        print (t)
        print ('request.body(unset_subjects)=')
        print (request.body)
        school = t.school

        data = json.loads(request.body)
        print ('data(unset_subjects)=')
        print (data)

        for key in data:
            print('key(unset_subjects)=' + key)
            subject = data[key]
            print('subject(unset_subjects)=' + subject)
            print ('now trying to extract subject(unset_subjects)')
            try:
                s = Subject.objects.get(school=school, subject_code=subject)
            except Exception as e:
                    print('unable to retrieve subject(unset_subjects)')
                    print ('Exception3 from teacher views.py = %s (%s)' % (e.message, type(e)))

            print ('now trying to unset teacher subject')

            try:
                ts = TeacherSubjects.objects.get(teacher=t, subject=s)
                if ts:
                    print('subject ' + s.subject_name + ' was set for this teacher '
                            + t.first_name + ' ' + t.last_name + '. This will now be deleted')
                    ts.delete()

            except Exception as e:
                print('subject ' + s.subject_name + ' was not set for teacher ' + t.first_name + ' ' + t.last_name)
                print ('Exception4 from teacher views.py = %s (%s)' % (e.message, type(e)))
                pass
        try:
            action = 'Subjects unSet'
            log_entry(teacher, action, 'Normal', True)
        except Exception as e:
            print('unable to create logbook entry')
            print ('Exception 501 from teachers views.py %s %s' % (e.message, type(e)))
    return HttpResponse('OK')