from django.shortcuts import render

# Create your views here.
import os
import json
import xlrd
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib import messages
from rest_framework import generics
from authentication.views import JSONResponse

from setup.models import School, Configurations
from student.models import Student
from teacher.models import Teacher
from student.serializers import StudentSerializer
from setup.forms import ExcelFileUploadForm
from .models import Bus_Rout, BusAttendanceTaken, Student_Rout, Attedance_Type, Bus_Attendance, BusStop

from .serializers import BusRoutSerializer, BusAttendanceSerializer, BusStopSerializer
from operations import sms


server_ip = 'http://52.32.99.184/'


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


def setup_routs(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Bus Routs'
    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                # determine the school for which this processing is done
                school_id = request.session['school_id']
                school = School.objects.get(id=school_id)
                print ('now starting to process the uploaded file for setting up Bus Routs...')
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
                    # skip the header rows
                    if row == 0:
                        continue

                    print ('Processing a new row')
                    bus_rout = sheet.cell(row, 0).value
                    print (bus_rout)

                    # Now we are ready to insert into db. But, we need to be sure that we are not trying
                    # to insert a duplicate
                    try:
                        c = Bus_Rout.objects.get(school=school, bus_root=bus_rout)
                        if c:
                            print ('Bus Rout ' + bus_rout + ' for school '
                                   + school.school_name + ' already exist. Hence skipping...')
                    except Exception as e:
                        print ('Exception1 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                        print ('Bus Rout ' + bus_rout + ' is a new rout. Hence inserting...')
                        try:
                            c = Bus_Rout(school=school, bus_root=bus_rout)
                            c.save()
                        except Exception as e:
                            print ('Exception2 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                            error = 'Unable to save the Bus Rout ' + bus_rout + ' for school ' \
                                    + school.school_name + ' in table Bus_Rout'
                            form.errors['__all__'] = form.error_class([error])
                            print (error)
                            return render(request, 'classup/setup_data.html', context_dict)

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Bus Routs Uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception3 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        # we are arriving at this page for the first time, hence show an empty form
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_bus_stops(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Bus Stops'
    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                # determine the school for which this processing is done
                school_id = request.session['school_id']
                school = School.objects.get(id=school_id)
                print ('now starting to process the uploaded file for setting up Bus stops...')
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
                    # skip the header rows
                    if row == 0:
                        continue

                    print ('Processing a new row')
                    stop_name = sheet.cell(row, 1).value
                    print (stop_name)
                    bus_rout = sheet.cell(row, 0).value
                    br = Bus_Rout.objects.get(school=school, bus_root=bus_rout)

                    # Now we are ready to insert into db. But, we need to be sure that we are not trying
                    # to insert a duplicate
                    try:
                        c = BusStop.objects.get(stop_name=stop_name, bus_rout=br)
                        if c:
                            print ('Bus Stop ' + stop_name + ' on bus rout ' +
                                   br.bus_root + ' already exist. Hence skipping...')
                    except Exception as e:
                        print ('Exception4 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                        print ('Bus stop  ' + stop_name + ' on rout ' +
                               br.bus_root + ' is a new stop. Hence inserting...')
                        try:
                            c = BusStop(stop_name=stop_name, bus_rout=br)
                            c.save()
                        except Exception as e:
                            print ('Exception5 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                            error = 'Unable to save the Bus stop ' + stop_name + 'on rout ' +\
                                    br.bus_root + ' in table Bus_Rout'
                            form.errors['__all__'] = form.error_class([error])
                            print (error)
                            return render(request, 'classup/setup_data.html', context_dict)

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Bus Stops uploaded. Please login from mobile app to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception6 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        # we are arriving at this page for the first time, hence show an empty form
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def student_bus_rout(request):
    context_dict = {

    }
    context_dict['user_type'] = 'school_admin'
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Upload Student Bus Rout Data'

    if request.method == 'POST':
        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                # determine the school for which this processing is done
                school_id = request.session['school_id']
                school = School.objects.get(id=school_id)
                print ('now starting to process the students bus rout mapping...')
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
                    bus_rout = sheet.cell(row, 3).value
                    stop_name = sheet.cell(row, 4).value

                    # start assigning student to bus routs. Both bus_rout and student are foreign objects

                    try:
                        the_rout = Bus_Rout.objects.get(school=school, bus_root=bus_rout)
                    except Exception as e:
                        error = 'Unable to retrieve the Bus Rout: ' + bus_rout
                        print ('Exception7 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        # todo - we should skip this student but report
                        # this and move on to the next student <provide code>
                        continue

                    try:
                        the_stop = BusStop.objects.get(stop_name=stop_name, bus_rout=the_rout)
                    except Exception as e:

                        error = 'Unable to retrieve the Bus stop: ' + stop_name
                        print ('Exception8 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        # todo - we should skip this student but report this and move on to the next student <provide code>
                        continue

                    try:
                        the_student = Student.objects.get(student_erp_id=student_id)
                    except Exception as e:
                        print ('Exception9 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                        error = 'Unable to retrieve the student: ' + student_id + ' ' + \
                                student_first_name + ' ' + student_last_name
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        # todo - we should skip this student but report this and move on to the next student <provide code>
                        continue

                    # process student first. If this is an existing student, this is an update operations.
                    try:
                        r = Student_Rout.objects.get(student=the_student)
                        if r:
                            print ('Student with  ID: ' + student_id +
                                   ' & name: ' + student_first_name + ' already exist. This will be updated!')
                            r.student = the_student
                            r.bus_root = the_rout
                            r.bus_stop = the_stop
                    except Exception as e:
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                        print ('Student with ID:  ' + student_id + ' Name: '
                               + student_first_name + ' ' + student_last_name +
                               ' is a new entry. Hence inserting...')
                        try:
                            r = Student_Rout(student=the_student, bus_root=the_rout, bus_stop=the_stop)
                            r.save()
                            print ('saving successful!')

                        except Exception as e:
                            error = 'Unable to create the new student-bus rout mapping in the database'
                            print (error)
                            print ('Exception10 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                            form.errors['__all__'] = form.error_class([error])
                            # todo - we should skip this student but report this and move on to the next student <provide code>
                    try:
                        r.save()
                        print ('updated Student with  ID: ' + student_id + ' & name: ' + student_first_name)

                    except Exception as e:
                        print ('Exception11 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                        error = 'Unable to save the bus rout mapping for Student with ID: ' + student_id + \
                                ' Name: ' + student_first_name + ' ' + student_last_name + ' in Table Student_Rout'
                        form.errors['__all__'] = form.error_class([error])
                        print (error)
                        # todo - we should skip this student but report this and move on to the next student <provide code>

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Bus Routs for ' + school.school_name +
                                 ' uploaded. Please login from device to verify')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                print ('Exception12 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                error = 'Invalid file uploaded. Please try again.'
                form.errors['__all__'] = form.error_class([error])
                print (error)
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


class RoutList(generics.ListAPIView):
    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        q = Bus_Rout.objects.filter(school=school).order_by('bus_root')
        return q

    serializer_class = BusRoutSerializer


class StudentListForRout1(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        bus_rout = self.kwargs['rout']
        the_rout = Bus_Rout.objects.get(school=school, bus_root=bus_rout)
        bus_stop = self.kwargs['bus_stop']
        the_stop = BusStop.objects.get(stop_name=bus_stop, bus_rout=the_rout)
        q = Student.objects.filter(student_rout__bus_root=the_rout,
                                   student_rout__bus_stop=the_stop).order_by('fist_name')
        return q


class StopListForRout(generics.ListAPIView):
    serializer_class = BusStopSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        bus_rout = self.kwargs['rout']
        the_rout = Bus_Rout.objects.get(school=school, bus_root=bus_rout)
        q = BusStop.objects.filter(bus_rout=the_rout).order_by('stop_name')
        return q


# this function is to verify whether an attendance on a bus rout for a particular date was taken earlier or not?
def attendance_taken_earlier(request, school_id, rout, d, m, y):
    if request.method == 'GET':
        return_data = {

        }
        the_date = date(int(y), int(m), int(d))
        try:
            school = School.objects.get(id=school_id)
            r = Bus_Rout.objects.get(school=school, bus_root=rout)

            q = BusAttendanceTaken.objects.filter(date=the_date, rout=r)
            if 0 == q.count():
                return_data['taken_earlier'] = False
            else:
                return_data['taken_earlier'] = True
            return JSONResponse(return_data, status=200)
        except Exception as e:
            print ('unable to check whether bus attendance was taken on ' + rout + ' on ' + str(the_date))
            print ('Exception13 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
    return JSONResponse(return_data, status=201)


@csrf_exempt
def bus_attendance_taken(request, school_id, rout, t, d, m, y, teacher):
    if request.method == 'POST':
        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        school = School.objects.get(id=school_id)
        r = Bus_Rout.objects.get(school=school, bus_root=rout)
        attendance_type = Attedance_Type.objects.get(route_type=t)

        the_date = date(int(y), int(m), int(d))

        # verify if the attendance for this rout, section, subject on this date has already been taken
        try:
            q = BusAttendanceTaken.objects.filter(date=the_date, rout=r, type=attendance_type)
            if 0 == q.count():
                a = BusAttendanceTaken(date=the_date)
                a.rout = r
                a.type = attendance_type
                a.taken_by = Teacher.objects.get(email=teacher)

                a.save()
        except Exception as e:
            print ('Exception14 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))

    return HttpResponse('OK')


class BusAttendanceList(generics.ListCreateAPIView):
    serializer_class = BusAttendanceSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        the_rout = self.kwargs['rout']
        rout_type = self.kwargs['type']
        d = self.kwargs['d']
        m = self.kwargs['m']
        y = self.kwargs['y']

        # all of the above except date are foreign key in Attendance model. Hence we need to get the actual object
        r = Bus_Rout.objects.get(school=school, bus_root=the_rout)
        t1 = Attedance_Type.objects.get(route_type='to_school')
        print (t1)
        t2 = Attedance_Type.objects.get(route_type='from_school')
        print (t2)

        q1 = Bus_Attendance.objects.filter(date=date(int(y), int(m), int(d)), bus_rout=r, attendance_type=t1)
        q2 = Bus_Attendance.objects.filter(date=date(int(y), int(m), int(d)), bus_rout=r, attendance_type=t2)

        te = BusAttendanceTaken.objects.filter(date=date(int(y), int(m), int(d)), rout=r, type=t2)
        print ('te count=')
        print (te.count())
        if rout_type == 'from_school':
            if te.count() > 0:
                print ('A')
                print (q2)
                return q2

            else:
                print ('B')
                return q1
        else:
            print ('C')
            return q1


@csrf_exempt
def delete_bus_attendance1(request, att_type, d, m, y):
    response_data = {

    }
    if request.method == 'POST':
        the_date = date(int(y), int(m), int(d))

        data = json.loads(request.body)
        print ('attendance correction data=')
        print (data)
        for key in data:
            st = data[key]
            # check whether the absence for this student for this date has been already marked or not
            try:
                student = Student.objects.get(id=st)
                attendance_type = Attedance_Type.objects.get(route_type=att_type)
                q = Bus_Attendance.objects.filter(date=the_date, student=student, attendance_type=attendance_type)
                if q.count() > 0:
                    q.delete()
            except Exception as e:
                print ('unable to delete the bus attendance for ' + student.fist_name + ' ' + student.last_name)
                print ('Exception15 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
        response_data['status'] = 'success'

    return JSONResponse(response_data, status=200)


@csrf_exempt
def process_bus_attendance1(request, att_type, d, m, y, teacher):
    response_data = {

    }
    if request.method == 'POST':
        the_date = date(int(y), int(m), int(d))
        try:
            attendance_type = Attedance_Type.objects.get(route_type=att_type)

        except Exception as e:
            print ('unable to retrieve attendance type for ' + att_type)
            print ('Exception16 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
        data = json.loads(request.body)
        print ('attendance processing data')
        print (data)
        for key in data:
            student = data[key]
            try:
                st = Student.objects.get(id=student)
                sr = Student_Rout.objects.get(student=st)
                bus_rout = sr.bus_root
                # check whether the attendance for this student for this date has been already marked or not

                q = Bus_Attendance.objects.filter(date=the_date,
                                                  student=st, bus_rout=bus_rout, attendance_type=attendance_type)
                if q.count() == 0:
                    bus_attendance = Bus_Attendance(date=the_date, student=st, bus_rout=bus_rout,
                                                    taken_by=Teacher.objects.get(email=teacher),
                                                    attendance_type=attendance_type)
                    bus_attendance.save()
            except Exception as e:
                print ('unable to save the bus attendance for ' + st.fist_name + ' ' + st.last_name +
                       ' for rout ' + bus_rout.bus_root + ' ' + attendance_type.rout_type
                       + 'on date ' + str(the_date))
                print ('Exception17 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
                response_data['status'] = 'failure'
            response_data['status'] = 'success'

    return JSONResponse(response_data, status=200)


@csrf_exempt
def report_delay(request):
    response = {

        }
    if request.method == 'POST':
        data = json.loads(request.body)
        school_id = data['school_id']
        rout = data['rout']
        teacher = data['teacher']
        message = data['message']

        try:
            school = School.objects.get(id=school_id)
            configuration = Configurations.objects.get(school=school)
            r = Bus_Rout.objects.get(school=school_id, bus_root=rout)
            teacher = Teacher.objects.get(email=teacher)
            email = teacher.email
            student_rout = Student_Rout.objects.filter(bus_root=r)

            school_name = school.school_name
            for sr in student_rout:
                parent = sr.student.parent
                m1 = parent.parent_mobile1
                m2 = parent.parent_mobile2

                full_message = 'Dear Ms/Mr ' + parent.parent_name + ', Delay on Bus rout ' + rout
                full_message += ': ' + message + '. Regards, ' + teacher.first_name + ' ' + teacher.last_name
                full_message += ', ' + school_name

                message_type = 'Bus Delay'
                sms.send_sms1(school, email, m1, full_message, message_type)

                if m2 != '':
                    if configuration.send_absence_sms_both_to_parent:
                        sms.send_sms1(school, email, m2, full_message, message_type)

                print (full_message)
        except Exception as e:
            print ('unable to send bus delay message')
            print ('Exception18 in bus_attendance views.py = %s (%s)' % (e.message, type(e)))
    return JSONResponse(response, status=200)