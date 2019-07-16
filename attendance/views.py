from django.shortcuts import render

# Create your views here.

import json
from datetime import date


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from .models import Attendance, AttendanceTaken, AttendanceUpdated, DailyAttendanceSummary
from academics.models import Section, Class, Subject
from student.models import Student
from teacher.models import Teacher
from setup.models import Configurations, School

from authentication.views import JSONResponse, log_entry

from .serializers import AttendanceSerializer

from operations import sms


class AttendanceList(generics.ListCreateAPIView):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)

        the_class = self.kwargs['class']
        section = self.kwargs['section']
        subject = self.kwargs['subject']
        print ('subject at the time of retrieving attendance=' + subject)
        d = self.kwargs['d']
        m = self.kwargs['m']
        y = self.kwargs['y']

        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        c = Class.objects.get(school=school, standard=the_class)
        s = Section.objects.get(school=school, section=section)
        sub = Subject.objects.get(school=school, subject_name=subject)

        q1 = Attendance.objects.filter(date=date(int(y), int(m), int(d)), the_class=c, section=s, subject=sub)
        return q1

    def post(self, request, *args, **kwargs):
        serializer = AttendanceSerializer(data=request.DATA)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)


# we need to make an entry into the AttendanceTaken table for any attendance that is taken. Why are we doing this?
# Because we only call process_attendance if a student is absent. If all students are present, process_attendance
# will not be called from device, hence there will be no entry in the Attendance table. Hence the excel file
# generated for Attendance of a month will not be accurate
@csrf_exempt
def attendance_taken(request, school_id, the_class, section, subject, d, m, y, teacher):
    if request.method == 'POST':
        school = School.objects.get(id=school_id)
        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        c = Class.objects.get(school=school, standard=the_class)
        print (c)
        s = Section.objects.get(school=school, section=section)
        print (s)
        sub = Subject.objects.get(school=school, subject_name=subject)
        print (sub)
        t = Teacher.objects.get(email=teacher)
        log_entry(teacher, "Attendance Taken Started", "Normal", True)

        print (t)

        the_date = date(int(y), int(m), int(d))
        print (the_date)

        # verify if the attendance for this class, section, subject on this date has already been taken
        try:
            q = AttendanceTaken.objects.filter(date=the_date, the_class=c, section=s, subject=sub)
            if 0 == q.count():
                log_entry(teacher, "Attendance not taken earlier", "Normal", True)
                a = AttendanceTaken(date=the_date)
                a.the_class = c
                a.section = s
                a.subject = sub
                a.taken_by = t

                a.save()
                log_entry(teacher, "Attendance Taken Recorded", "Normal", True)
        except Exception as e:
            print ('failed to recored AttendanceTaken')
            print ('Exception1 from attendance views.py = %s (%s)' % (e.message, type(e)))
            log_entry(teacher, "failed to recored AttendanceTaken. Exception 1 from attendance views.py",
                      "Normal", False)

        # for the purpose of audit, make an entry in AttendanceUpdated table.
        try:
            au = AttendanceUpdated(date=the_date, the_class=c, section=s, subject=sub, updated_by=t)
            au.save()
            log_entry(teacher, "Attendance Updated recorded", "Normal", True)
        except Exception as e:
            print ('failed to record AttendanceUpdate')
            print ('Exception2 from attendance views.py = %s (%s)' % (e.message, type(e)))
            log_entry(teacher, "failed to record AttendanceUpdate. Exepction 2 from attendance views.py",
                      "Normal", False)
    return HttpResponse('OK')


@csrf_exempt
def process_attendance1(request, school_id, the_class, section, subject, d, m, y, teacher):
    response_data = {

    }
    message_type = 'Attendance'

    if request.method == 'POST':
        log_entry(teacher, "Attendance Processing Started", "Normal", True)
        school = School.objects.get(id=school_id)

        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        c = Class.objects.get(school=school, standard=the_class)
        s = Section.objects.get(school=school, section=section)
        sub = Subject.objects.get(school=school, subject_name=subject)
        the_date = date(int(y), int(m), int(d))
        t = Teacher.objects.get(email=teacher)
        teacher_name = '%s %s' % (t.first_name, t.last_name)
        today = date.today()
        time_delta = today - the_date
        print('this attendance taken by %s for class %s-%s for subject %s is %i days old' %
              (teacher_name, the_class, section, subject, time_delta.days))

        data = json.loads(request.body)
        print (data)
        absent = 0
        for key in data:
            student_id = data[key]
            student = Student.objects.get(id=student_id)
            student_name = '%s %s' % (student.fist_name, student.last_name)

            absent += 1

            # check to see if absence for this student for this date, class, section and subject has already
            #  been marked
            try:
                q = Attendance.objects.filter(date=the_date, the_class=c, section=s, subject=sub, student=student)

                # make an entry to database only it is a fresh entry
                #if q.count() == 0:
                if not Attendance.objects.filter(date=the_date, the_class=c,
                                                 section=s, subject=sub, student=student).exists():
                    action = 'Absence marked for %s %s' % (student.fist_name, student.last_name)
                    print(action)

                    attendance = Attendance(date=the_date)
                    attendance.the_class = c
                    attendance.section = s
                    attendance.subject = sub
                    attendance.student = student
                    attendance.taken_by = t

                    attendance.save()
                    log_entry(teacher, action, "Normal", True)
                    action = 'Starting to send sms to parents of  ' + student.fist_name + ' ' + student.last_name
                    log_entry(teacher, action, "Normal", True)
                    # send sms to the parents of absent students
                    m1 = ''
                    m2 = ''
                    try:
                        p = student.parent
                        m1 = p.parent_mobile1
                        m2 = p.parent_mobile2
                    except Exception as e:
                        print ('Exception occured during processing of: ')
                        print (student)
                        print ('Exception3 from attendance views.py = %s (%s)' % (e.message, type(e)))
                        log_entry(teacher, "Attendance Processing Error. Exception 3 from attendance views.py",
                                  "Normal", True)

                    print ("mobile1=" + m1)
                    print ("mobile2=" + m2)

                    message = ''
                    configuration = Configurations.objects.get(school=school)
                    school_name = school.school_name
                    school_short_name = configuration.school_short_name

                    # 14/04/2018 - for collage students, SMS will be sent to students
                    institute_type = configuration.type

                    try:
                        parent_name = student.parent.parent_name
                        # prepare the message
                        action = 'Absence SMS Drafting for ' + parent_name + ' started'
                        log_entry(teacher, action, "Normal", True)

                        # 17/02/17 we are looking to use student first name in messages.
                        # However, some schools store entire name as first name. T
                        # his need to be checke and split first name if entire name is stored as first name
                        the_name = student.fist_name
                        if ' ' in student.fist_name:
                            (f_name, l_name) = the_name.split(' ')
                        else:
                            f_name = the_name
                        if institute_type == 'Collage':
                            message = 'Dear %s, you' % the_name
                        else:
                            message = 'Dear ' + parent_name + ', your ward ' + f_name

                        if institute_type == 'Collage':
                            if time_delta.days == 0:
                                message += ' are'
                            else:
                                message += ' were'
                        else:
                            if time_delta.days == 0:
                                message += ' is'
                            else:
                                message += ' was'

                        # if subject is main then we need to tell that student was absent
                        if subject == 'Main' or subject == 'main' or subject == 'MAIN':

                            message += ' absent on ' + str(d) + '/' + str(m) + '/' + str(y)
                        else:
                            message += ' absent on ' + str(d) + '/' + str(m) + '/' + str(y) + \
                                       ' in the attendance of ' + subject
                        # 04/05/2017 - coaching classes does not require application for absence
                        if configuration.type != 'school':
                            message += '. Regards %s ' % school_short_name
                        else:
                            message += '. Please send an application (Ignore if already done). Regards, ' + school_short_name
                    except Exception as e:
                        print ('Exception4 from attendance views.py = %s (%s)' % (e.message, type(e)))
                        action = 'Error in drafting SMS for ' + parent_name + '. Exception 4 from attendance views.py'
                        log_entry(teacher, action,"Normal", True)

                    print (message)

                    # 10/02/2018 - absence SMS will not be sent if attendance is for a date older than 7 days
                    if time_delta.days < 7:
                        print('this attendance is recent. Hence SMS will be sent')
                        # for coaching classes and colleges we need to send sms for any kind of absence
                        if configuration.send_period_bunk_sms:

                            sms.send_sms1(school, teacher, m1, message, message_type)
                            action = 'Absence SMS sent to ' + parent_name
                            log_entry(teacher, action, "Normal", True)
                            if m2 != '':
                                if configuration.send_absence_sms_both_to_parent:
                                    sms.send_sms1(school, teacher, m2, message, message_type)
                                    log_entry(teacher, action, "Normal", True)
                        else:
                            # for schools
                            # if this subject is NOT the main subject, then we will send sms only if the student was present
                            # in main attendance (means the student has BUNKED this class :)
                            if subject != 'Main' and subject != 'main' and subject != 'MAIN':
                                try:
                                    main = Subject.objects.get(school=school, subject_name='Main')
                                    q = Attendance.objects.filter(date=the_date, the_class=c,
                                                                  section=s, subject=main, student=student)
                                    if q.count() == 0:
                                        print (student.fist_name + ' ' + student.last_name +
                                               '  was not absent in Main attendance. '
                                               'Looks he has bunked this class...')
                                        action = student.fist_name + ' ' + student.last_name
                                        action += ' found to be bunking the Class!!!'
                                        log_entry(teacher, action, "Normal", True)
                                        if configuration.send_period_bunk_sms:
                                            sms.send_sms1(school, teacher, m1, message, message_type)
                                            action = 'Absence SMS sent to ' + student.parent.parent_name
                                            log_entry(teacher, action, "Normal", True)
                                            if m2 != '':
                                                if configuration.send_absence_sms_both_to_parent:
                                                    sms.send_sms1(school, teacher, m2, message, message_type)
                                                    action = 'Absence SMS sent to Mrs. ' + student.parent.parent_name
                                                    log_entry(teacher, action, "Normal", True)
                                except Exception as e:
                                    action = 'Unable to send SMS to ' + student.parent.parent_name
                                    log_entry(teacher, action, "Normal", True)
                                    print ('unable to send sms for ' + f_name)
                                    print ('Exception5 from attendance views.py = %s (%s)' % (e.message, type(e)))
                            else:
                                if configuration.send_absence_sms:
                                    sms.send_sms1(school, teacher, m1, message, message_type)
                                    action = 'Absence SMS sent to ' + student.parent.parent_name
                                    log_entry(teacher, action, "Normal", True)
                                    if m2 != '':
                                        if configuration.send_absence_sms_both_to_parent:
                                            sms.send_sms1(school, teacher, m2, message, message_type)
                                            action = 'Absence SMS sent to Mrs. ' + student.parent.parent_name
                                            log_entry(teacher, action, "Normal", True)
                    else:
                        print('this attendance is more than 7 days old. Hence not sending SMS')
                else:
                    print('absence for %s for %s in %s has already been marked.' % (student_name, the_date, subject))
            except Exception as e:
                print ('Exception6 from attendance views.py = %s (%s)' % (e.message, type(e)))
                log_entry(teacher, "Absence was already marked. Exception 6 from attendance views.py", "Normal", True)

        # 16/07/2019 we are implementing table to store daily attendance summaries.
        # So that download attendance summary is fast
        print('now storing the attendance summary for')
        try:
            total = Student.objects.filter(current_class=c, current_section=s).count()
            print('total students in %s-%s of %s  = %i' % (the_class, section, school, total))
            present = total - absent
            percentage = int(round((float(present) / float(total)) * 100, 0))
            print(percentage)
            print('students present on %s = %i' % (the_date, percentage))
            try:
                summary = DailyAttendanceSummary.objects.get(date=the_date, the_class=c,
                                                             section=s, subject=sub)
                summary.total = total
                summary.present = present
                summary.absent = absent
                summary.percentage = percentage
                summary.save()
                print('attendance summary for class %s-%s of %s date %s is updated' %
                      (the_class, section, school, the_date))
            except Exception as ex:
                print('exception 16072019-X from attendance views.py %s %s' % (ex.message, type(ex)))
                summary = DailyAttendanceSummary(date=the_date, the_class=c, section=s, subject=sub)
                summary.total = total
                summary.present = present
                summary.absent = absent
                summary.percentage = percentage
                summary.save()
                print('attendance summary for class %s-%s of %s date %s is stored' %
                      (the_class, section, school, the_date))
        except Exception as ex:
            print('exception 16072019-B from attendance views.py %s (%s)' % (ex.message, type(ex)))
            print('failed in storing the attendance summary for %s-%s of %s' % (the_class, section, school))
    response_data['status'] = 'success'
    log_entry(teacher, "Attendance Processing Complete", "Normal", True)
    return JSONResponse(response_data, status=200)


# we need to exempt this view from csrf verification. Will be updated in next version when
# we will implement authentication
@csrf_exempt
def delete_attendance2(request, school_id, the_class, section, subject, d, m, y):
    response_data = {

    }
    if request.method == 'POST':
        school = School.objects.get(id=school_id)
        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        c = Class.objects.get(school=school, standard=the_class)
        s = Section.objects.get(school=school, section=section)
        sub = Subject.objects.get(school=school, subject_name=subject)

        the_date = date(int(y), int(m), int(d))
        print (the_date)
        data = json.loads(request.body)
        print ('correction list=')
        print (data)
        for key in data:
            student_id = data[key]
            student = Student.objects.get(id=student_id)

            # check to see if absence for this student for this date, class, section and subject has already been marked
            try:
                q = Attendance.objects.filter(date=the_date, the_class=c,
                                              section=s, subject=sub, student=student)
                print (q.count())
                # make an entry to database only it is a fresh entry
                if q.count() > 0:
                    try:
                        q1 = q[:1].get()
                        teacher = q1.taken_by.email
                        q.delete()

                        action = 'Deleted a previously taken attendance for ' +\
                                 student.fist_name + ' ' + student.last_name
                        log_entry(teacher, action, "Normal", True)
                    except Exception as e:
                        print ('Exception 7 from attendance views.py = %s (%s)' % (e.message, type(e)))

            except Exception as e:
                print ('Exception 9 from attendance views.py = %s (%s)' % (e.message, type(e)))

        # this view is being called from mobile. We use dummy template so that we dont' run into exception
        # return render(request, 'classup/dummy.html')
        response_data['status'] = 'success'
        return JSONResponse(response_data, status=200)