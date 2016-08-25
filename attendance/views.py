from django.shortcuts import render

# Create your views here.

import json
from datetime import date


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from .models import Attendance, AttendanceTaken
from academics.models import Section, Class, Subject
from student.models import Student
from teacher.models import Teacher
from setup.models import Configurations, School

from authentication.views import JSONResponse

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
        print (t)

        the_date = date(int(y), int(m), int(d))
        print (the_date)

        # verify if the attendance for this class, section, subject on this date has already been taken
        try:
            q = AttendanceTaken.objects.filter(date=the_date, the_class=c, section=s, subject=sub)
            if 0 == q.count():
                a = AttendanceTaken(date=the_date)
                a.the_class = c
                a.section = s
                a.subject = sub
                a.taken_by = t

                a.save()
        except Exception as e:
            print ('Exception = %s (%s)' % (e.message, type(e)))

    return HttpResponse('OK')


# we need to exempt this view from csrf verification. Will be updated in next version when
# we will implement authentication
@csrf_exempt
def process_attendance(request, the_class, section, subject, d, m, y, id, teacher):
    if request.method == 'POST':
        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        c = Class.objects.get(standard=the_class)
        s = Section.objects.get(section=section)
        sub = Subject.objects.get(subject_name=subject)
        student = Student.objects.get(id=id)
        the_date = date(int(y), int(m), int(d))
        t = Teacher.objects.get(email=teacher)

        # check to see if absence for this student for this date, class, section and subject has already been marked
        try:
            q = Attendance.objects.filter(date=the_date, the_class=c, section=s, subject=sub, student=student)

            # make an entry to database only it is a fresh entry
            if q.count() == 0:
                attendance = Attendance(date=the_date)
                attendance.the_class = c
                attendance.section = s
                attendance.subject = sub
                attendance.student = student
                attendance.taken_by = t

                attendance.save()

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
                    print ('Exception = %s (%s)' % (e.message, type(e)))

                print ("mobile1=" + m1)
                print ("mobile2=" + m2)

                message = ''

                # prepare the message
                try:
                    configuration = Configurations.objects.get(pk=1)
                    school_name = configuration.school_name
                    student_name = student.fist_name + ' ' + student.last_name
                    message = 'Dear Parent, your ward ' + student_name

                    # if subject is main then we need to tell that student was absent
                    if subject == 'Main' or subject == 'main' or subject == 'MAIN':
                        message += ' was absent today'
                    else:
                        message += ' was absent today in the attendance of ' + subject

                    message += '. Please ignore if you have already '
                    message += 'submitted an application for this absence. '
                    message += 'Otherwise, please send an application. Regards, ' + school_name
                    message += ' Administration.'
                except Exception as e:
                    print ('Exception = %s (%s)' % (e.message, type(e)))

                print (message)

                # if this subject is NOT the main subject, then we will send sms only if the student was present
                # in main attendance (means the student has BUNKED this class :)
                if subject != 'Main' and subject != 'main' and subject != 'MAIN':

                    try:
                        main = Subject.objects.get(subject_name='Main')
                        q = Attendance.objects.filter(date=the_date, the_class=c,
                                                      section=s, subject=main, student=student)

                        if q.count() == 0:
                            print ('this student was not absent in Main attendance. '
                                   'Looks he has bunked this class...')
                            sms.send_sms(m1, message)
                            if m2 != '':
                                sms.send_sms(m2, message)
                    except Exception as e:
                        print ('unable to send sms for ' + student_name)
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                else:
                    sms.send_sms(m1, message)
                    if m2 != '':
                        sms.send_sms(m2, message)

        except Exception as e:
            print ('Exception = %s (%s)' % (e.message, type(e)))

    # this view is being called from mobile. We use dummy template so that we dont' run into exception
    # return render(request, 'classup/dummy.html')
    return HttpResponse('OK')


@csrf_exempt
def process_attendance1(request, school_id, the_class, section, subject, d, m, y, teacher):
    response_data = {

    }
    if request.method == 'POST':
        school = School.objects.get(id=school_id)
        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        c = Class.objects.get(school=school, standard=the_class)
        s = Section.objects.get(school=school, section=section)
        sub = Subject.objects.get(school=school, subject_name=subject)
        the_date = date(int(y), int(m), int(d))
        t = Teacher.objects.get(email=teacher)

        data = json.loads(request.body)
        print (data)
        for key in data:
            student_id = data[key]
            student = Student.objects.get(id=student_id)

            # check to see if absence for this student for this date, class, section and subject has already been marked
            try:
                q = Attendance.objects.filter(date=the_date, the_class=c, section=s, subject=sub, student=student)

                # make an entry to database only it is a fresh entry
                if q.count() == 0:
                    attendance = Attendance(date=the_date)
                    attendance.the_class = c
                    attendance.section = s
                    attendance.subject = sub
                    attendance.student = student
                    attendance.taken_by = t

                    attendance.save()

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
                        print ('Exception = %s (%s)' % (e.message, type(e)))

                    print ("mobile1=" + m1)
                    print ("mobile2=" + m2)

                    message = ''
                    configuration = Configurations.objects.get(school=school)
                    school_name = school.school_name

                    # prepare the message
                    try:
                        parent_name = student.parent.parent_name
                        student_name = student.fist_name + ' ' + student.last_name
                        message = 'Dear Ms/Mr ' + parent_name + ', your ward ' + student_name

                        # if subject is main then we need to tell that student was absent
                        if subject == 'Main' or subject == 'main' or subject == 'MAIN':
                            message += ' was absent on ' + str(d) + '/' + str(m) + '/' + str(y)
                        else:
                            message += ' was absent on ' + str(d) + '/' + str(m) + '/' + str(y) + \
                                       ' in the attendance of ' + subject

                        message += '. Please ignore if you have already '
                        message += 'submitted an application for this absence. '
                        message += 'Otherwise, please send an application. Regards, ' + school_name
                        # message += ' Administration.'
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))

                    print (message)

                    # for coaching classes and colleges we need to send sms for any kind of absence
                    if configuration.send_period_bunk_sms:
                        sms.send_sms(m1, message)
                        if m2 != '':
                            sms.send_sms(m2, message)
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
                                    print ('this student was not absent in Main attendance. '
                                           'Looks he has bunked this class...')
                                    if configuration.send_period_bunk_sms:
                                        sms.send_sms(m1, message)
                                        if m2 != '':
                                            sms.send_sms(m2, message)
                            except Exception as e:
                                print ('unable to send sms for ' + student_name)
                                print ('Exception = %s (%s)' % (e.message, type(e)))
                        else:
                            if configuration.send_absence_sms:
                                sms.send_sms(m1, message)
                                if m2 != '':
                                    sms.send_sms(m2, message)
            except Exception as e:
                print ('Exception = %s (%s)' % (e.message, type(e)))


    # this view is being called from mobile. We use dummy template so that we dont' run into exception
    # return render(request, 'classup/dummy.html')
    response_data['status'] = 'success'
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
                q = Attendance.objects.filter(date=the_date, the_class=c, section=s, subject=sub, student=student)
                print (q.count())
                # make an entry to database only it is a fresh entry
                if q.count() > 0:
                    q.delete()

            except Exception as e:
                print ('Exception = %s (%s)' % (e.message, type(e)))

        # this view is being called from mobile. We use dummy template so that we dont' run into exception
        # return render(request, 'classup/dummy.html')
        response_data['status'] = 'success'
        return JSONResponse(response_data, status=200)


# we need to exempt this view from csrf verification. Will be updated in next version when
# we will implement authentication
@csrf_exempt
def delete_attendance(request, the_class, section, subject, d, m, y, id):
    if request.method == 'POST':
        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        c = Class.objects.get(standard=the_class)
        print c
        s = Section.objects.get(section=section)
        print s
        sub = Subject.objects.get(subject_name=subject)
        print sub
        student = Student.objects.get(id=id)
        print student
        the_date = date(int(y), int(m), int(d))
        print the_date

        # check to see if absence for this student for this date, class, section and subject has already been marked
        try:
            q = Attendance.objects.filter(date=the_date, the_class=c,
                           section=s, subject=sub, student=student)
            print q.count()
            # make an entry to database only it is a fresh entry
            if q.count() > 0:
                q.delete()

        except Exception as e:
            print 'Exception = %s (%s)' % (e.message, type(e))

    # this view is being called from mobile. We use dummy template so that we dont' run into exception
    # return render(request, 'classup/dummy.html')
    return HttpResponse('OK')
