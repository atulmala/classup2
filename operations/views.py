from datetime import datetime, date

import MySQLdb
import urllib
import time
import calendar
from calendar import monthrange
import StringIO
import base64
import urllib2

import json

import xlsxwriter

from django.contrib.auth.models import User
from django.db import DataError
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.core.files.base import ContentFile

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from authentication.views import JSONResponse, log_entry, LoginRecord
from academics.models import Class, Section, Subject, ClassTest, TestResults, ClassTeacher
from student.models import Student
from teacher.models import Teacher, TeacherMessageRecord, MessageReceivers, Staff
from attendance.models import Attendance, AttendanceTaken, DailyAttendanceSummary
from parents.models import ParentCommunication
from setup.models import Configurations, School, GlobalConf
from pic_share.models import ImageVideo, ShareWithStudents, SharedWithTeacher

from formats.formats import Formats as format

from .models import SMSRecord, ClassUpAdmin
from .serializers import SMSDetailSerializer
from .forms import SchoolAttSummaryForm, AttendanceRegisterForm
from .forms import TestResultForm, ParentsCommunicationDetailsForm, BulkSMSForm, SMSSummaryForm
import sms


# Create your views here.


def operations_index():
    pass


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class CommitBulkSMS(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        print('Starting to send bulk sms')
        try:
            # connect to the database
            try:
                # db = MySQLdb.connect('35.194.43.14', 'classup', 'classup', 'classup2')
                db = MySQLdb.connect('classup-mysql.ce7idolzs1jo.us-east-2.rds.amazonaws.com',
                                     'classup', 'classup#1', 'classup2')
                cursor1 = db.cursor()

                # extract the list of all sms for which api_called = false
                sql1 = "select id, sender_code, recipient_number, message from operations_smsrecord " \
                       "where api_called = 0 and message_type = 'Bulk SMS (Web Interface)'"
                cursor1.execute(sql1)
            except Exception as e:
                print('exception 29032018-A from send_bulk_sms.py %s (%s)' % (e.message, type(e)))
                print('failed to establish sql connection or executing sql')

            # send messages one by one
            row = cursor1.fetchone()
            while row is not None:
                id = row[0]
                sender_id = row[1]
                mobile = row[2]
                message = row[3]

                m1 = message.replace(" ", "+")
                print(m1)
                m2 = m1.replace("&", "%26")
                print(m2)

                url = 'http://softsms.in/app/smsapi/index.php?'
                key = '58fc1def26489'
                url += 'key=%s' % key
                url += '&type=Text'
                url += '&contacts=%s' % mobile
                url += '&senderid=%s' % sender_id
                url += '&msg=%s' % m2
                print('url=%s' % url)
                print(url)

                try:
                    print('sending to=' + mobile)
                    print('message received in send_bulk_sms.py=' + message)

                    response = urllib.urlopen(url)
                    print('response = ')
                    message_id = response.read()
                    print(message_id)

                    # update the smsrecord table that this message has been sent
                    try:
                        cursor2 = db.cursor()
                        sql2 = "UPDATE operations_smsrecord SET api_called = 1, outcome ='" + message_id
                        sql2 += "' WHERE id=" + str(id)
                        print(sql2)
                        cursor2.execute(sql2)
                        db.commit()
                        cursor2.close()
                    except Exception as e:
                        print('Error while trying to update the delivery status of sms with message_id = ' + message_id)
                        print ('Exception3 from operations get_sms_dlvry_status.py = %s (%s) %s' % (
                            e.message, type(e), e.args))
                except Exception as e:
                    print ('Exception1 from send_bulk_sms.py = %s (%s)' % (e.message, type(e)))
                    print('failed to send message: ' + message + ' to mobile number: ' + str(mobile))

                row = cursor1.fetchone()

            cursor1.close()
            db.close()
            return HttpResponse()
        except Exception as e:
            print('Error 2 from send_bulk_sms.py')
            print('Exception2 from send_bulk_sms.py = %s (%s)' % (e.message, type(e)))
            return HttpResponse()


class SMSHistoryList(generics.ListAPIView):
    serializer_class = SMSDetailSerializer

    def get_queryset(self):
        recipient = self.kwargs['parent_mobile']
        try:
            action = 'Retrieving SMS History'
            log_entry(recipient, action, 'Normal', True)
        except Exception as e:
            print('unable to create logbook entry')
            print('Exception 500 from operations views.py = %s (%s)' % (e.message, type(e)))
        q = SMSRecord.objects.filter(recipient_number=recipient). \
            exclude(message_type='Forgot Password').order_by('-date')
        return q


def att_summary_school_device(request):
    print('inside att_summary_school_device')
    dict_attendance_summary = {

    }

    response_array = []

    if request.method == 'GET':
        school_id = request.GET.get('school_id')
        try:
            school = School.objects.get(id=school_id)
        except Exception as e:
            print ('unable to fetch the school for school with id:  ' + school_id)
            print ('Exception 400 from operations views.py = %s (%s)' % (e.message, type(e)))

        dt = request.GET.get('date')
        mn = request.GET.get('month')
        yr = request.GET.get('year')
        the_date = date(int(yr), int(mn), int(dt))

        main = Subject.objects.get(school=school, subject_name='Main')

        grand_total = p_total = a_total = 0

        for c in Class.objects.filter(school=school):
            for s in Section.objects.filter(school=school):
                # check to see if this class/section combination exist in this school or not
                total = Student.objects.filter(current_class=c, current_section=s, active_status=True).count()

                if 0 != total:  # class/section exist
                    grand_total += total
                    print('class = ' + c.standard + ' ' + s.section)
                    # check whether attendance for this class/section has been taken yet or not?
                    att_taken = AttendanceTaken.objects.filter(date__day=dt, date__month=mn, date__year=yr, the_class=c,
                                                               section=s, subject=main).count()
                    if 0 == att_taken:  # attendance was not taken for this class/section
                        dict_attendance_summary['class'] = c.standard + ' ' + s.section
                        dict_attendance_summary['attendance'] = 'Not Taken'
                        dict_attendance_summary['percentage'] = 'N/A'
                        d = dict(dict_attendance_summary)
                        response_array.append(d)
                        continue

                    # attendance has been taken for this class/section
                    dict_attendance_summary['class'] = c.standard + ' ' + s.section

                    # 17/07/2019 - as we have implemented table to store attendance calculations to speed
                    # up the download, first check if the data exists in the table
                    try:
                        print('first try to retrieve attendance summary for %s on %s from AttendanceSummary Table' %
                              (school, the_date))
                        summary = DailyAttendanceSummary.objects.get(date=the_date, the_class=c,
                                                                     section=s, subject=main)
                        total = summary.total
                        present = summary.present
                        dict_attendance_summary['attendance'] = '%i/%i' % (present, total)
                        percentage = summary.percentage
                        dict_attendance_summary['percentage'] = str(percentage) + '%'
                        d = dict(dict_attendance_summary)
                        response_array.append(d)

                        p_total += present
                    except Exception as e:
                        print('exception 17072019-A from operations views.py %s %s' % (e.message, type(e)))
                        print('attendance summary for %s for %s is to be fetched the old way' % (school, the_date))
                        absent = Attendance.objects.filter(date__day=dt, date__month=mn, date__year=yr,
                                                           the_class=c, section=s, subject=main).count()
                        present = total - absent
                        dict_attendance_summary['attendance'] = str(present) + '/' + str(total)

                        perc_present = int(round((float(present) / float(total)) * 100, 0))
                        dict_attendance_summary['percentage'] = str(perc_present) + '%'
                        d = dict(dict_attendance_summary)
                        response_array.append(d)

                        p_total += present
                        a_total += absent
        dict_attendance_summary['class'] = 'Total'
        dict_attendance_summary['attendance'] = str(p_total) + '/' + str(grand_total)
        if p_total == 0:
            grand_present_perc = 'N/A'
        else:
            grand_present_perc = int(round((float(p_total) / float(grand_total)) * 100, 0))
        dict_attendance_summary['percentage'] = str(grand_present_perc) + '%'
        d = dict(dict_attendance_summary)
        response_array.append(d)

    return JSONResponse(response_array, status=200)


def att_summary_school(request):
    context_dict = {
    }
    context_dict['header'] = 'Daily Class-wise Attendance Summary'
    context_dict['school_name'] = request.session['school_name']

    if request.session['user_type'] == 'school_admin':
        context_dict['user_type'] = 'school_admin'

    # first see whether the cancel button was pressed
    if "cancel" in request.GET:
        return render(request, 'classup/setup_index.html', context_dict)

    if "submit" in request.GET:
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)
        the_date = request.GET['date']
        if the_date == '':
            error = 'Please select a date'
            context_dict['error'] = error
            form = SchoolAttSummaryForm()
            context_dict['form'] = form
            form.errors['__all__'] = form.error_class([error])
            return render(request, 'classup/daily_att_summary.html', context_dict)

        converted_date = datetime.strptime(the_date, "%m/%d/%Y").strftime("%Y-%m-%d")
        dmy_date = datetime.strptime(the_date, "%m/%d/%Y").strftime("%d-%m-%Y")

        # setup the excel file for download
        excel_file_name = 'Attendance_Summary_' + str(dmy_date) + '.xlsx'
        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        summary_sheet = workbook.add_worksheet("Summary")
        absentee_sheet = workbook.add_worksheet("Absentee List")

        title = workbook.add_format(format.get_title())
        header = workbook.add_format(format.get_header())
        cell_center = workbook.add_format(format.get_cell_center())
        cell_left = workbook.add_format(format.get_cell_left())
        perc_format = workbook.add_format(format.get_perc_format())
        grand_perc_format = workbook.add_format({
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'top',
            'bold': True,
            'border': 1
        })
        summary_row = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'top',
            'border': 1
        })
        title_text = u"{0} {1}".format(ugettext("Attendance Summary for "), str(dmy_date))
        summary_sheet.merge_range('A1:H1', title_text, title)
        summary_sheet.write(2, 0, ugettext("S No."), header)
        summary_sheet.write(2, 1, ugettext("Class"), header)
        summary_sheet.write(2, 2, ugettext("Section"), header)
        summary_sheet.write(2, 3, ugettext("Total Students"), header)
        summary_sheet.write(2, 4, ugettext("Present"), header)
        summary_sheet.write(2, 5, ugettext("Absent"), header)
        summary_sheet.write(2, 6, ugettext("% Presence"), header)

        title_text2 = u"{0} {1}".format(ugettext("List of Absent Students on "), str(dmy_date))
        absentee_sheet.merge_range('B1:H1', title_text2, title)
        absentee_sheet.write(2, 0, ugettext("Class"), header)
        absentee_sheet.write(2, 1, ugettext("Section"), header)
        absentee_sheet.write(2, 2, ugettext("Absent Students"), header)
        absentee_sheet.write(2, 3, ugettext("Regn No"), header)
        absentee_sheet.write(2, 4, ugettext("Parent Name"), header)
        absentee_sheet.write(2, 5, ugettext("Parent Mobile"), header)

        # columns Total Present and % Attendance are to be made wider
        summary_sheet.set_column('D:D', 15)
        summary_sheet.set_column('G:G', 15)

        absentee_sheet.set_column('C:C', 20)
        absentee_sheet.set_column('D:F', 15)

        main = Subject.objects.get(school=school, subject_name='Main')

        grand_total = p_total = a_total = idx = 0

        # start fetching the data and write into the excel file
        row_absentee = 3
        for c in Class.objects.filter(school=school):
            for s in Section.objects.filter(school=school):

                total = Student.objects.filter(current_class=c, current_section=s, active_status=True).count()
                grand_total += total
                row = 3 + idx

                if 0 != total:
                    print('class = %s-%s' % (c.standard, s.section))
                    # check whether attendance for this class/section has been taken yet or not?
                    att_taken = AttendanceTaken.objects.filter(date=converted_date, the_class=c,
                                                               section=s, subject=main).count()
                    if 0 == att_taken:
                        summary_sheet.write_number(row, 0, idx + 1, cell_center)
                        summary_sheet.write_string(row, 1, c.standard, cell_center)
                        summary_sheet.write_string(row, 2, s.section, cell_center)
                        summary_sheet.write_number(row, 3, total, cell_center)
                        merge_range = 'E' + str(row + 1) + ':' + 'G' + str(row + 1)
                        summary_sheet.merge_range(merge_range, "Attendance Not Taken", summary_row)

                        idx += 1
                        continue

                    absent = Attendance.objects.filter(date=converted_date,
                                                       the_class=c, section=s, subject=main).count()
                    present = total - absent
                    perc_present = float(float(present) / float(total))

                    p_total += present
                    a_total += absent
                    grand_present_perc = float(float(p_total) / float(grand_total))

                    summary_sheet.write_number(row, 0, idx + 1, cell_center)
                    summary_sheet.write_string(row, 1, c.standard, cell_center)
                    summary_sheet.write_string(row, 2, s.section, cell_center)
                    summary_sheet.write_number(row, 3, total, cell_center)
                    summary_sheet.write_number(row, 4, present, cell_center)
                    summary_sheet.write_number(row, 5, absent, cell_center)
                    summary_sheet.write_number(row, 6, perc_present, perc_format)

                    idx += 1

                    # Print the name of absent students, their regn number, parent name & mobile
                    absentee_sheet.write_string(row_absentee, 0, c.standard, cell_center)
                    absentee_sheet.write_string(row_absentee, 1, s.section, cell_center)
                    for student in Attendance.objects.filter(date=converted_date,
                                                             the_class=c, section=s, subject=main):
                        absentee_sheet.write_string(row_absentee, 2,
                                                    student.student.fist_name + ' ' + student.student.last_name,
                                                    cell_left)
                        absentee_sheet.write_string(row_absentee, 3, student.student.student_erp_id, cell_left)
                        absentee_sheet.write_string(row_absentee, 4, student.student.parent.parent_name, cell_left)
                        absentee_sheet.write_string(row_absentee, 5, student.student.parent.parent_mobile1, cell_left)
                        row_absentee += 1
                    # to make a gap between rows of subsequent classes
                    row_absentee += 1
        if 0 != p_total:
            merge_range = 'A' + str(row + 1) + ':' 'C' + str(row + 1)
            summary_sheet.merge_range(merge_range, "Grand Total", summary_row)
            summary_sheet.write_number(row, 3, grand_total, summary_row)
            summary_sheet.write_number(row, 4, p_total, summary_row)
            summary_sheet.write_number(row, 5, a_total, summary_row)
            summary_sheet.write_number(row, 6, grand_present_perc, grand_perc_format)

        workbook.close()

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response

    if request.method == 'GET':
        form = SchoolAttSummaryForm()
        context_dict['form'] = form
    else:
        form = SchoolAttSummaryForm()
        context_dict['form'] = form

    return render(request, 'classup/daily_att_summary.html', context_dict)


class MonthlySMSReport(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    context_dict = {'header': 'Monthly SMS Report'}

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        print(data)
        school_id = data['school_id']
        school = School.objects.get(pk=school_id)
        school_name = school.school_name

        the_date = data['date']

        m = the_date.split('-')[1]
        month_int = int(m)
        print('month_int = %d' % month_int)
        month = calendar.month_name[month_int]
        y = the_date.split('-')[0]
        year_int = int(y)
        print('year_int = %d' % year_int)

        excel_file_name = 'SMS_Report_' + '_' + str(month) + '_' + str(y) + '.xlsx'

        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        sms_sheet = workbook.add_worksheet("SMS Summary")

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
        text_format = workbook.add_format({
            'text_wrap': True})

        title_text = 'Monthly SMS Report for ' + school_name
        title_text += ' for ' + month + '/' + y

        f = workbook.add_format()
        f.set_align('top')
        sms_sheet.merge_range('A2:Q2', title_text, title)
        sms_sheet.set_column('A:A', 4)
        sms_sheet.set_column('B:B', 10)
        sms_sheet.set_column('C:C', 15)
        sms_sheet.set_column('D:D', 10)
        sms_sheet.set_column('E:E', 15)
        sms_sheet.set_column('F:F', 15)
        sms_sheet.set_column('G:G', 10)
        sms_sheet.set_column('H:H', 100)
        sms_sheet.set_column('I:I', 15)
        sms_sheet.set_column('J:J', 20)
        sms_sheet.set_column('K:K', 20)

        current_row = 3
        sms_sheet.write(3, 0, ugettext("S No."), header)
        sms_sheet.write(3, 1, ugettext("Date"), header)
        sms_sheet.write(3, 2, ugettext("Sender"), header)
        sms_sheet.write(3, 3, ugettext("Sender Type"), header)
        sms_sheet.write(3, 4, ugettext("Recipient"), header)
        sms_sheet.write(3, 5, ugettext("Recipient Number"), header)
        sms_sheet.write(3, 6, ugettext("Recipient Type"), header)
        sms_sheet.write(3, 7, ugettext("Message"), header)
        sms_sheet.write(3, 8, ugettext("Message Type"), header)
        sms_sheet.write(3, 9, ugettext("Status/Job ID"), header)
        sms_sheet.write(3, 10, ugettext("Credits Consumed"), header)
        try:
            sms_list = SMSRecord.objects.filter(school=school, date__month=month_int,
                                                date__year=year_int).order_by('-date')
            print('successfully retrieved the monthly sms queryset for %s for the month of %s-%s' %
                  (school_name, str(month), str(y)))
            print('sms_list = ')
            print(sms_list)
            sr_no = 1
            for s in sms_list:
                current_row += 1
                sms_sheet.write_number(current_row, 0, sr_no)

                # the date on which the sms was sent
                try:
                    sms_date = s.date
                    iso_date = sms_date.isoformat()
                    d, t = iso_date.split('T')
                    date_time = '%s %s' % (d, t[:8])
                    # print('date_time = %s' % date_time)
                    # sms_sheet.write(current_row, 1, sms_date, date_format)
                    sms_sheet.write(current_row, 1, date_time, text_format)
                except Exception as e:
                    print('exception 05122018-A from operations views.py %s %s' % (e.message, type(e)))
                    print('unable to insert date in the monthly sms report for %s for the month %s-%s' %
                          (school_name, str(month), str(y)))

                # sender of the sma
                sender = s.sender1
                sms_sheet.write(current_row, 2, ugettext(sender), text_format)

                # sender type
                sender_type = s.sender_type
                sms_sheet.write(current_row, 3, ugettext(sender_type), text_format)

                # recipient of the message
                recipient = s.recipient_name
                sms_sheet.write(current_row, 4, ugettext(recipient), text_format)

                # recipient number
                recipient_number = s.recipient_number
                sms_sheet.write(current_row, 5, ugettext(recipient_number), text_format)

                # recipient type
                recipient_type = s.recipient_type
                sms_sheet.write(current_row, 6, ugettext(recipient_type), text_format)

                # message
                message = s.message
                sms_sheet.write(current_row, 7, ugettext(message), text_format)

                # message type
                message_type = s.message_type
                sms_sheet.write(current_row, 8, ugettext(message_type), text_format)

                if message_type == 'Forgot Password':
                    message = '<Contents Hidden>'  # don't show the password in the Excel sheet
                    sms_sheet.write(current_row, 7, ugettext(message), text_format)

                status = s.status
                sms_sheet.write(current_row, 9, ugettext(status))

                # calculate the sms credits consumed by this sms
                total_char = len(message)
                sms_credits = total_char / 160
                additional = total_char % 160
                if additional > 0:
                    sms_credits += 1

                sms_sheet.write_number(current_row, 10, sms_credits)

                sr_no += 1

            workbook.close()
            print('workbook closed')
        except Exception as e:
            print('unable to write sms to excel file')
            print ('Exception50 from operations views.py = %s (%s)' % (e.message, type(e)))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())

        return response


class AttRegisterClass(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    context_dict = {
    }
    context_dict['header'] = 'Download Monthly Attendance'

    def post(self, request, *args, **kwargs):
        print("IP Address for debug-toolbar: " + request.META['REMOTE_ADDR'])
        data = json.loads(request.body)
        print(data)
        school_id = data['school_id']
        school = School.objects.get(pk=school_id)

        try:
            standard = data['the_class']
            the_class = Class.objects.get(school=school, standard=standard)

            sec = data['section']
            section = Section.objects.get(school=school, section=sec)

            the_subject = data['subject']

            the_date = data['date']
        except Exception as e:
            print('exception 17112019-A from operations views.py %s %s' % (e.message, type(e)))
            print('failed to decode json')
        print(the_date)
        m = the_date.split('-')[1]
        month_int = int(m)
        month = calendar.month_name[month_int]
        y = the_date.split('-')[0]
        year_int = int(y)

        excel_file_name = 'Attendance_Resigter_' + str(the_class.standard) + '_' + str(section.section)
        excel_file_name += '_' + str(the_subject) + '_' + str(month) + '_' + str(y) + '.xlsx'
        print('excel file to be generated with name = %s' % excel_file_name)

        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        attendance_sheet = workbook.add_worksheet("Attendance")
        attendance_sheet.set_landscape()
        attendance_sheet.set_paper(9)  # A4 paper
        attendance_sheet.fit_to_pages(1, 0)
        attendance_sheet.set_footer('&L%s' % 'Class Teacher Signature......................')

        fmt = format()
        title = workbook.add_format(fmt.get_title())
        header = workbook.add_format(fmt.get_header())
        cell_normal = workbook.add_format(fmt.get_cell_normal())
        cell_center = workbook.add_format(fmt.get_cell_center())
        cell_left = workbook.add_format(fmt.get_cell_left())
        cell_total = workbook.add_format(fmt.get_cell_total())
        present_format = workbook.add_format(fmt.get_present_format())
        absent_format = workbook.add_format(fmt.get_absent_format())
        holiday_format = workbook.add_format(fmt.get_holiday_format())
        perc_format = workbook.add_format(fmt.get_perc_format())

        title_text = 'Monthly Attendance for Class ' + the_class.standard + '-' + section.section + \
                     ', Subject: ' + str(the_subject)
        title_text += ' for ' + month + '/' + y
        attendance_sheet.merge_range('A2:Q2', title_text, title)
        attendance_sheet.set_column('A:A', 7)
        attendance_sheet.set_column('B:B', 7)
        attendance_sheet.set_column('C:C', 15)
        attendance_sheet.set_column('D:AG', 3)
        attendance_sheet.set_column('AH:AI', 5)

        attendance_sheet.write(3, 0, ugettext("Roll No."), header)
        attendance_sheet.write(3, 1, ugettext("Reg No."), header)
        attendance_sheet.write(3, 2, ugettext("Name"), header)
        attendance_sheet.set_default_row(14, hide_unused_rows=True)

        # Next 28/29/30/31 columns will be for dates. We need to get the number fo days in the month
        DayL = ['M', 'Tu', 'W', 'Th', 'F', 'Sa', 'Su']

        days = monthrange(year_int, month_int)[1]
        for d in range(1, days + 1):
            date_for_db = date(year_int, month_int, int(d))
            the_day = DayL[date_for_db.weekday()]

            attendance_sheet.write(2, d + 2, ugettext(the_day), header)
            attendance_sheet.write_number(3, d + 2, d, header)
        attendance_sheet.write(3, days + 3, ugettext("Total"), header)
        attendance_sheet.write(3, days + 4, ugettext("%"), header)
        attendance_sheet.write(3, days + 5, ugettext("Till Date"), header)
        attendance_sheet.write(3, days + 6, ugettext("Till Date %"), header)

        idx = 0
        row = 4 + idx

        # 04/08/2016 - Changed functionality to retrieve attendance for a specific subject. Done for coaching/college
        subject = Subject.objects.get(school=school, subject_name=the_subject)

        # we will cache the list of holidays so that the execution is faster, and less hits to db means
        # saving on AWS bill!
        holidays = []

        holiday_count = present_count = 0
        db_hit = 1
        for s in Student.objects.filter(school=school, current_class=the_class,
                                        current_section=section, active_status=True).order_by('fist_name'):
            print('\ndealing with: %s %s' % (s.fist_name, s.last_name))
            attendance_sheet.write_number(row, 0, idx + 1, cell_center)
            reg_no = s.student_erp_id
            print(reg_no)
            attendance_sheet.write_string(row, 1, reg_no, cell_center)
            attendance_sheet.write_string(row, 2, ugettext(s.fist_name + ' ' + s.last_name), cell_left)

            db_hit += 1
            for d in range(1, days + 1):
                date_for_db = date(year_int, month_int, int(d))
                if d not in holidays:
                    try:
                        a = AttendanceTaken.objects.filter(date=date_for_db,
                                                           the_class=the_class, section=section, subject=subject)
                        db_hit += 1
                        if 0 < a.count():  # this means this date was not a holiday :( and attendance was taken
                            # check if this student was present in the class that day or was in a cinema hall or mall :)
                            try:
                                q = Attendance.objects.filter(date=date_for_db, student=s,
                                                              the_class=the_class, section=section, subject=subject)
                                db_hit += 1
                                if 0 < q.count():  # student bunked this class!
                                    attendance_sheet.write_string(row, d + 2, ugettext("A"), absent_format)
                                else:  # student was getting bored attending this lecture
                                    attendance_sheet.write_string(row, d + 2, ugettext("P"), present_format)
                                    present_count += 1
                            except Exception as e:
                                print ('exception occured while doing lookup in the Attendance table')
                                print ('Exception1 from operations views.py = %s (%s)' % (e.message, type(e)))
                        else:  # wow, this day was a holiday
                            holidays.append(d)
                            holiday_count += 1
                            attendance_sheet.write(row, d + 2, ugettext("NA"), holiday_format)
                    except Exception as e:
                        print ('exception occured while doing lookup in the AttendanceTaken table')
                        print ('Exception2 from operations views.py = %s (%s)' % (e.message, type(e)))
                else:
                    attendance_sheet.write(row, d + 2, ugettext("NA"), holiday_format)

                working_days = days - holiday_count
                attendance_sheet.write_string(row, d + 3,
                                              ugettext(str(present_count) + '/' + str(working_days)), cell_total)
                try:
                    perc_present = float(float(present_count) / float(working_days))
                    attendance_sheet.write_number(row, d + 4, perc_present, perc_format)
                except Exception as e:
                    print ('exception occured while trying to calculate percentage')
                    print ('Exception3 from operations views.py = %s (%s)' % (e.message, type(e)))

            # calculate the till date attendance for this student
            try:
                conf = Configurations.objects.get(school=school)
                session_start_month = conf.session_start_month
                print('the session start month is %i' % session_start_month)
                if month_int < session_start_month:
                    start = date(year_int - 1, session_start_month, 1)
                else:
                    start = date(year_int, session_start_month, 1)
                print('start = ')
                print(start)
                no_of_days = calendar.monthrange(year_int, month_int)[1]
                end = date(year_int, month_int, no_of_days)
                print('end = ')
                print(end)

                q = AttendanceTaken.objects.filter(the_class=the_class, section=section,
                                                   subject=subject, date__range=[start, end])
                working_days_till_date = q.count()
                print('total working days till date: %i' % working_days_till_date)

                q = Attendance.objects.filter(student=s, subject=subject, date__range=[start, end])
                absent_days_till_date = q.count()
                print('absent days till date: %i' % absent_days_till_date)
                present_days_till_date = working_days_till_date - absent_days_till_date
                print('present days till date: %i' % present_days_till_date)
                attendance_sheet.write(row, d + 5,
                                       ugettext(str(present_days_till_date) + '/' + str(working_days_till_date)),
                                       cell_total)
                if int(working_days_till_date) < 1:
                    present_perc_till_date = 'N/A'
                    attendance_sheet.write_string(row, d + 6, present_perc_till_date)
                else:
                    present_perc_till_date = float(float(present_days_till_date) / float(working_days_till_date))
                    attendance_sheet.write(row, d + 6, present_perc_till_date, perc_format)
            except Exception as e:
                print ('unable to calculate attendance till date')
                print ('Exception4 from operations views.py = %s (%s)' % (e.message, type(e)))

            row += 1
            idx += 1
            present_count = 0

        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response


@csrf_exempt
def send_bulk_sms(request):
    context_dict = {
    }
    context_dict['header'] = 'Send Bulk SMS'
    context_dict['user_type'] = 'school_admin'
    staff = None

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print('Bulk SMS process initiated from device')
            message_type = 'Bulk SMS (Device)'
            school_id = data['school_id']
            sender = data['user']
            message_body = data['message_text']

            whole_school = data['whole_school']
            if whole_school != 'true':
                selected_classes = data['classes_array']
            else:
                selected_classes = ['All Classes']

            try:
                image_included = data['image_included']
                print('image_included = %s' % image_included)
            except Exception as e:
                print('exception 21082019-A from operations views.py %s %s' % (e.message, type(e)))
                print('the user has not yet updated to the latest app version')
                image_included = 'no'

            if image_included == 'yes':
                image = data['image']
                image_name = data['image_name']
                print('image_name = %s' % image_name)
                image_file = ContentFile(base64.b64decode(image), name=image_name.replace('@', '').replace(' ', '_'))
        except Exception as e:
            print('exception 13112019-A from operations views.py %s %s' % (e.message, type(e)))
            print('json not present, means this is request from vue.js web admin interface')

            message_type = 'Bulk SMS (Web Interface)'
            print('Bulk SMS process initiated from vue.js admin web interface')
            school_id = request.POST.get('school_id')
            sender = request.POST.get('user')
            message_body = request.POST.get('message_text')
            whole_school = request.POST.get('whole_school')
            sc = str(request.POST.get('classes_array')).split()
            selected_classes = sc[0].split(',')
            print(selected_classes)
            print map(str, selected_classes)

            image_included = request.POST.get('image_included')
            print('image_included = %s' % image_included)
            if image_included == 'true' or image_included == 'yes':
                image_file = request.FILES['file']
                print(type(image_file))
                print('image_file = %s' % image_file)
                print(image_file)
                image_name = request.POST.get('image_name').replace(' ', '_')

        school = School.objects.get(id=school_id)
        if whole_school == "true":
            selected_classes = Class.objects.filter(school=school)

        print(str(selected_classes))
        print(type(selected_classes))
        description = message_body

        if image_included == 'true' or image_included == 'yes':
            # 14/11/2019 - need to make sure that 'dev' to be changed to 'prod' when this code is pushed to production
            long_link = 'https://storage.cloud.google.com/classup/classup2/media/prod/image_video/%s' % \
                        image_name.replace('@', '')
            # long_link = 'https://storage.cloud.google.com/classup/classup2/media/dev/image_video/%s' % \
            #             image_name.replace('@', '')

            print('long_link = %s' % long_link)
            short_link = long_link

            # prepare short link
            global_conf = GlobalConf.objects.get(pk=1)
            key = global_conf.short_link_api
            url = 'https://cutt.ly/api/api.php?'
            url += 'key=%s&short=%s' % (key, long_link)
            print('url for generating short link = %s' % url)
            try:
                response = urllib2.urlopen(url)
                print('response for generating short link = %s' % response)
                outcome = json.loads(response.read())
                print('ouctome = ')
                print(outcome)
                status = outcome['url']['status']
                print('status = %i' % status)
                if status == 7:
                    short_link = outcome['url']['shortLink']
                    print('short_lint = %s' % short_link)
            except Exception as e:
                print('exception 20082019-A from operations views.py %s %s' % (e.message, type(e)))
                print('failed to generate short link  for the image/video uploaded by %s' % sender)

    start_time = time.time()

    # send to parents
    try:
        configuration = Configurations.objects.get(school=school)
        for sc in selected_classes:
            print('class = ' + str(sc))
            if sc != 'Teachers' and sc != 'Staff':
                the_class = Class.objects.get(school=school, standard=sc)
                sections = Section.objects.filter(school=school)
                for section in sections:
                    print('section = %s' % section)
                    if image_included == 'yes' or image_included == 'true':
                        try:
                            image_video = ImageVideo()
                            print('image_file = ')
                            print(image_file)
                            image_video.location = image_file
                            if len(message_body) > 200:
                                image_video.descrition = message_body[0:190]
                            else:
                                image_video.descrition = message_body
                            image_video.the_class = the_class
                            image_video.section = section
                            print('short_link = %s' % short_link)
                            image_video.short_link = short_link
                            image_video.save()

                        except DataError as e:
                            print('exception 20082019-B from operations views.py %s %s' % (e.message, type(e)))
                            print('error in saving image/video for admin broadcast')
                    student_list = Student.objects.filter(current_class=the_class, current_section=section,
                                                          active_status=True)
                    start_time = time.time()
                    for student in student_list:
                        student_name = '%s %s' % (student.fist_name, student.last_name)
                        parent = student.parent
                        if configuration.type == 'Collage':
                            message = 'Dear %s, ' % student_name
                        else:
                            message = 'Dear %s, ' % parent.parent_name

                        if image_included == 'yes' or image_included == 'true':
                            try:
                                shared = ShareWithStudents(image_video=image_video,
                                                           student=student, the_class=the_class, section=section)
                                shared.save()
                                message += '%s. link: %s Regards, %s' % \
                                           (message_body, short_link, configuration.school_short_name)
                            except Exception as e:
                                print('exception 20082019-C from operations views.py %s %s' %
                                      (e.message, type(e)))
                                print('failed to save SharedWithStudent object')
                        else:
                            message += message_body + ' Regards, ' + configuration.school_short_name
                            print(message)
                        mobile = parent.parent_mobile1
                        sms.send_sms1(school, sender, mobile, message, message_type)

                        if configuration.send_absence_sms_both_to_parent:
                            mobile = parent.parent_mobile2
                            if mobile != '':
                                sms.send_sms1(school, sender, mobile, message, message_type)
            if sc == 'Teachers':
                staff = ['teacher']
            if sc == 'Staff':
                if staff is not None:
                    staff.append('Staff')
                else:
                    staff = ['Staff']
    except Exception as e:
        print('Exception 255 from opertions views.py = %s (%s)' % (e.message, type(e)))
        print('failed to send sms to parents of students of selected classes')

    # send to teachers/staff
    print('now sending bulk sms to teacher & staff')
    if staff is not None:
        if image_included == 'yes' or image_included == 'true':
            try:
                image_video = ImageVideo()
                image_video.location = image_file
                image_video.descrition = message_body
                image_video.short_link = short_link
                image_video.save()
                print('image saved')
            except Exception as e:
                print('exception 22082019-B from operations views.py %s %s' % (e.message, type(e)))
                print('error in saving image/video for admin broadcast')
        for st in staff:
            print('st = ' + str(st))
            if st == 'teacher' or st == 'Teachers':
                for teacher in Teacher.objects.filter(school=school):
                    teacher_name = teacher.first_name + ' ' + teacher.last_name
                    print(teacher_name)
                    message = 'Dear ' + teacher_name + ', '
                    if image_included == 'yes' or image_included == 'true':
                        try:
                            shared_with_teacher = SharedWithTeacher(image_video=image_video, teacher=teacher)
                            shared_with_teacher.save()
                        except Exception as e:
                            print('exception 22082019-C from operations views.py %s %s' % (e.message, type(e)))
                            print('error in saving image/video for admin broadcast')
                        message += '%s. link: %s Regards, %s' % \
                                   (message_body, short_link, configuration.school_short_name)
                    else:
                        message += message_body + ' Regards, ' + configuration.school_short_name
                    print(message)
                    teacher_mobile = teacher.mobile
                    print(teacher_mobile)
                    sms.send_sms1(school, sender, teacher_mobile, message, message_type)
            if st == 'staff' or st == 'Staff':
                for staff in Staff.objects.filter(school=school):
                    staff_name = '%s %s' % (staff.first_name, staff.last_name)
                    print(staff_name)
                    message = 'Dear ' + staff_name + ', '
                    if image_included == 'yes':
                        try:
                            shared_with_teacher = SharedWithTeacher(image_video=image_video, staff=staff)
                            shared_with_teacher.save()
                        except Exception as e:
                            print('exception 22082019-D from operations views.py %s %s' % (e.message, type(e)))
                            print('error in saving image/video for admin broadcast')
                        message += '%s. link: %s Regards, %s' % \
                                   (message_body, short_link, configuration.school_short_name)
                    else:
                        message += message_body + ' Regards, ' + configuration.school_short_name
                    print(message)
                    staff_mobile = staff.mobile
                    print(staff_mobile)
                    sms.send_sms1(school, sender, staff_mobile, message, message_type)

    # 23/10/2018 - there was a demand that if whole school is chosen then send to
    # teachers & staff (18/02/2019)as well
    try:
        if whole_school == 'true':
            for teacher in Teacher.objects.filter(school=school):
                teacher_name = teacher.first_name + ' ' + teacher.last_name
                print(teacher_name)
                message = 'Dear ' + teacher_name + ', '
                if image_included == 'yes' or image_included == 'true':
                    message += '%s. link: %s Regards, %s' % \
                               (message_body, short_link, configuration.school_short_name)
                else:
                    message += message_body + ' Regards, ' + configuration.school_short_name
                print(message)
                teacher_mobile = teacher.mobile
                print(teacher_mobile)
                sms.send_sms1(school, sender, teacher_mobile, message, message_type)
            print('sent bulk sms message: %s : to all the teachers of %s' % (message, school.school_name))

            for staff in Staff.objects.filter(school=school):
                staff_name = '%s %s' % (staff.first_name, staff.last_name)
                print(staff_name)
                message = 'Dear ' + staff_name + ', '
                if image_included == 'yes' or image_included == 'true':
                    message += '%s. link: %s Regards, %s' % \
                               (message_body, short_link, configuration.school_short_name)
                else:
                    message += message_body + ' Regards, ' + configuration.school_short_name
                print(message)
                staff_mobile = staff.mobile
                print(staff_mobile)
                sms.send_sms1(school, sender, staff_mobile, message, message_type)
            print('sent bulk sms message: %s : to all the staff of %s' % (message, school.school_name))
    except Exception as e:
        print('exception 23102018-A from operations views.py %s %s' % (e.message, type(e)))
        print('trying to send bulk sms to teachers of %s but failed' % school.school_name)

    elapsed_time = time.time() - start_time
    print('time taken to send sms=' + str(elapsed_time))

    # 11/02/17 - As we have made bulk sms sending a batch process, we need to send an sms to ClassUp Admin
    # reminding to run the batch job
    print('now sending sms to ClassUp Admin to run the batch process to deliver bulk sms...')
    try:
        ca = ClassUpAdmin.objects.get(pk=1)
        admin_mobile = ca.admin_mobile
        print(admin_mobile)
        if message_type == 'Bulk SMS (Web Interface)':
            message1 = '%s has initiated bulk sms process through Web Interface. ' % school
            message1 += 'Run the batch. Message was: "%s"' % message_body
        else:
            message1 = '%s has initiated bulk sms process through Device Interface. ' % school
            message1 += 'Message was: "%s"' % message_body
        print(message1)
        message_type = 'Run Batch'
        sms.send_sms1(school, sender, admin_mobile, message1, message_type)
    except Exception as e:
        print('Failed to retrieve the mobile number of ClassUp Admin. '
              'Cannot send sms for running the batch process for sending bulk sms')
        print('Exception 125 fron operations views.py = %s (%s)' % (e.message, type(e)))

    context_dict['header'] = 'Operation Completed'
    messages.success(request, 'Messages Sent!')

    context_dict['status'] = 'success'
    context_dict['outcome'] = 'Messages Sent'
    return JSONResponse(context_dict, status=200)


@csrf_exempt
def send_message(request, school_id):
    response = {

    }
    message_type = 'Teacher Communication'
    school = School.objects.get(id=school_id)
    configuration = Configurations.objects.get(school=school)
    include_link = False
    try:
        data = json.loads(request.body)
        print(data)
        print("originated from device")
        from_device = True

        message_content = data['message']

        # 19/12/2019 - if coming from Activity Group Communication the json may not contain whole_class key
        try:
            whole_class = data['whole_class']
            if whole_class == "true":
                the_class = data["class"]
                the_section = data["section"]
                c = Class.objects.get(school=school, standard=the_class)
                sec = Section.objects.get(school=school, section=the_section)
        except Exception as e:
            print('exception 19122019-A from operations views.py %s %s' % (e.message, type(e)))
            print('this message might have originated from Activity Group communication')

        email = data['teacher']
        t = Teacher.objects.get(email=email)

        try:
            coming_from = data['coming_from']
            print ('coming_from = %s' % coming_from)
        except Exception as e:
            print ('exception 261117-B from operations views.py %s %s' % (e.message, type(e)))
            print ('coming_from not set. This means this is a Teacher Communication')
            coming_from = 'TeacherCommunication'
    except Exception as e:
        print('exception 14122019-A from operations views.py %s %s' % (e.message, type(e)))
        print("json not present. This message triggered from vue.js web teacher interface")
        from_device = False
        coming_from = request.POST.get('coming_from')
        message_content = request.POST.get('message')
        email = request.POST.get('teacher')
        t = Teacher.objects.get(email=email)
        whole_class = request.POST.get('whole_class')
        the_class = request.POST.get('class')
        the_section = request.POST.get('section')
        c = Class.objects.get(school=school, standard=the_class)
        sec = Section.objects.get(school=school, section=the_section)

        image_included = request.POST.get('image_included')
        if image_included == 'true' or image_included == 'yes':
            include_link = True
            image_file = request.FILES['file']
            print(type(image_file))
            print('image_file = %s' % image_file)
            print(image_file)
            image_name = request.POST.get('image_name').replace(' ', '_')
            # long_link = 'https://storage.cloud.google.com/classup/classup2/media/prod/image_video/%s' % \
            #             image_name.replace('@', '')
            long_link = 'https://classup2.s3.us-east-2.amazonaws.com/media/prod/image_video/%s' % \
                        image_name.replace('@', '')
            print('long_link = %s' % long_link)
            short_link = long_link

            # prepare short link
            global_conf = GlobalConf.objects.get(pk=1)
            key = global_conf.short_link_api
            url = 'https://cutt.ly/api/api.php?'
            url += 'key=%s&short=%s' % (key, long_link)
            print('url for generating short link = %s' % url)
            try:
                response = urllib2.urlopen(url)
                print('response for generating short link = %s' % response)
                outcome = json.loads(response.read())
                print('ouctome = ')
                print(outcome)
                status = outcome['url']['status']
                print('status = %i' % status)
                if status == 7:
                    short_link = outcome['url']['shortLink']
                    print('short_lint = %s' % short_link)
            except Exception as e:
                print('exception 14122019-B-A from operations views.py %s %s' % (e.message, type(e)))
                print('failed to generate short link  for the image/video uploaded by %s' % email)

            try:
                image_video = ImageVideo()
                print('image_file = ')
                print(image_file)
                image_video.location = image_file
                image_video.descrition = message_content
                image_video.teacher = t
                image_video.the_class = c
                image_video.section = sec
                image_video.short_link = short_link
                image_video.save()
            except Exception as e:
                print('exception 20082019-E from operations views.py %s %s' % (e.message, type(e)))
                print('error in saving image/video for admin broadcast')

    # create record for Teacher messages history
    teacher_record = TeacherMessageRecord(teacher=t, message=message_content)
    teacher_name = t.first_name + ' ' + t.last_name
    message_trailer = '. Regards, ' + teacher_name + ', ' + configuration.school_short_name

    if coming_from == 'TeacherCommunication':
        # check if the message is to be sent to all the parents
        if whole_class == "true":
            teacher_record.sent_to = 'Whole Class'
            teacher_record.the_class = the_class
            teacher_record.section = the_section
            teacher_record.save()

            try:
                action = 'Sending message to whole class ' + the_class + '-' + the_section
                action += ', Message: ' + message_content
                log_entry(email, action, 'Normal', True)
            except Exception as e:
                print('unable to create logbook entry')
                print ('Exception 500 from operations views.py %s %s' % (e.message, type(e)))

            # get the list of all students in this class/section
            try:
                student_list = Student.objects.filter(current_class=c, current_section=sec, active_status=True)
                print(student_list)
                for s in student_list:
                    p = s.parent
                    m1 = p.parent_mobile1
                    m2 = p.parent_mobile2
                    the_name = s.fist_name

                    if ' ' in s.fist_name:
                        (f_name, l_name) = the_name.split(' ')
                    else:
                        f_name = the_name
                    message_header = 'Dear ' + p.parent_name + ', message regarding ' + \
                                     f_name + ': '
                    if include_link:
                        message_content += '. link: %s  ' % short_link
                        try:
                            shared = ShareWithStudents(image_video=image_video,
                                                       student=s, the_class=c, section=sec)
                            shared.save()
                        except Exception as e:
                            print('exception 14122019-C from operations views.py %s %s' %
                                  (e.message, type(e)))
                        print('failed to save SharedWithStudent object')
                    message = message_header + message_content + message_trailer
                    print ('message = ' + message)
                    message_receiver = MessageReceivers(teacher_record=teacher_record,
                                                        student=s, full_message=message)
                    sms.send_sms1(school, email, m1, message, message_type, receiver=message_receiver)
                    message_receiver.save()

                    if configuration.send_absence_sms_both_to_parent:
                        if m2 != '':
                            sms.send_sms1(school, email, m2, message, message_type)
            except Exception as e:
                print ('Unable to send message while trying for whole class')
                print ('Exception11 from operations views.py = %s (%s)' % (e.message, type(e)))
            response["status"] = "success"

        # the message is to be sent to parents of selected students only
        else:
            if not from_device:
                print('from vue.js web interface to selected students')
                data = {

                }
                recepients = request.POST.get('recepients')
                recepients = recepients.split(',')
                print(recepients)

                for recepient in recepients:
                    print(recepient)
                    data[recepient] = recepient
                print(data)

            teacher_record.sent_to = 'Selected Students'
            for key in data:
                if (key != 'message') and (key != 'teacher') \
                        and (key != 'whole_class') and (key != 'coming_from'):
                    try:
                        action = 'Sending message to Selected Students. Message:  '
                        action += message_content
                        log_entry(email, action, 'Normal', True)
                    except Exception as e:
                        print('unable to create logbook entry')
                        print ('Exception 501 from operations views.py %s %s' % (e.message, type(e)))
                    student_id = data[key]

                    s = Student.objects.get(pk=student_id)
                    try:
                        teacher_record.the_class = s.current_class.standard
                        teacher_record.section = s.current_section.section
                        teacher_record.save()
                    except Exception as e:
                        print ('exception 291117-B from operations views.py %s %s' % e.message, type(e))
                        print ('error occured while trying to save teacher_record')
                    p = s.parent
                    m1 = p.parent_mobile1
                    print (m1)
                    m2 = p.parent_mobile2
                    print (m2)

                    try:
                        the_name = s.fist_name
                        if ' ' in s.fist_name:
                            (f_name, l_name) = the_name.split(' ')
                        else:
                            f_name = the_name
                    except Exception as e:
                        print('exception 16082018 from operations views.py %s (%s)' % (e.message, type(e)))
                        print('unable to extract firts name for %s %s' % (s.fist_name, s.last_name))
                        f_name = s.fist_name

                    if configuration.type == 'Collage':
                        student_name = '%s %s' % (s.fist_name, s.last_name)
                        message_header = 'Dear %s, ' % student_name
                    else:
                        message_header = 'Dear ' + p.parent_name + ', message regarding ' + \
                                         f_name + ': '

                    if include_link:
                        message_content += '. link: %s  ' % short_link
                        try:
                            shared = ShareWithStudents(image_video=image_video,
                                                       student=s, the_class=c, section=sec)
                            shared.save()
                        except Exception as e:
                            print('exception 14122019-D from operations views.py %s %s' %
                                  (e.message, type(e)))
                    message = message_header + message_content + message_trailer
                    print ('message = ' + message)

                    try:
                        message_receiver = MessageReceivers(teacher_record=teacher_record,
                                                            student=s, full_message=message)
                        sms.send_sms1(school, email, m1, message, message_type, receiver=message_receiver)
                        message_receiver.save()
                        try:
                            action = 'SMS sent to ' + p.parent_name + ' (' + p.parent_mobile1 + ')'
                            action += ', Message: ' + message_content
                            log_entry(email, action, 'Normal', True)
                        except Exception as e:
                            print('unable to create logbook entry')
                            print ('Exception 502 from operations views.py %s %s' % (e.message, type(e)))
                        if configuration.send_absence_sms_both_to_parent:
                            if m2 != '':
                                sms.send_sms1(school, email, m2, message, message_type)
                                try:
                                    action = 'SMS sent to ' + p.parent_name + ' (' + p.parent_mobile2 + ')'
                                    action += ', Message: ' + message_content
                                    log_entry(email, action, 'Normal', True)
                                except Exception as e:
                                    print('unable to create logbook entry')
                                    print ('Exception 503 from operations views.py %s %s' %
                                           (e.message, type(e)))
                    except Exception as e:
                        print ('Unable to send message to ' + p.parent_name + 'with mobile number: ' + m1)
                        print ('Exception12 from operations views.py = %s (%s)' % (e.message, type(e)))

            response["status"] = "success"
    if coming_from == 'ActivityGroup':
        print('Activity Group communication')
        from activity_groups.models import ActivityGroup, ActivityMembers
        group_id = data['group_id']
        print('group_id = %s' % group_id)
        try:
            group = ActivityGroup.objects.get(id=group_id)
            teacher_record.sent_to = group.group_name
            teacher_record.activity_group = group.group_name
            teacher_record.save()
        except Exception as e:
            print('exception 09092019-A from operations view.py %s %s' % (e.message, type(e)))
            print('failed to save teacher record')
        try:
            members_list = ActivityMembers.objects.filter(group=group)
            print(members_list)
            for member in members_list:
                p = member.student.parent
                m1 = p.parent_mobile1
                m2 = p.parent_mobile2
                the_name = member.student.fist_name

                if ' ' in member.student.fist_name:
                    (f_name, l_name) = the_name.split(' ')
                else:
                    f_name = the_name
                message_header = 'Dear ' + p.parent_name + ', message regarding ' + \
                                 f_name + ': '
                message = message_header + message_content + message_trailer
                print ('message = ' + message)
                message_receiver = MessageReceivers(teacher_record=teacher_record,
                                                    student=member.student, full_message=message)
                sms.send_sms1(school, email, m1, message, message_type, receiver=message_receiver)
                if configuration.send_absence_sms_both_to_parent:
                    if m2 != '':
                        sms.send_sms1(school, email, m2, message, message_type)
        except Exception as e:
            print ('Unable to send message while trying for Group')
            print ('Exception 251117-A from operations views.py = %s (%s)' % (e.message, type(e)))
        response["status"] = "success"
    return JSONResponse(response, status=200)


def test_result(request):
    context_dict = {
    }
    context_dict['header'] = 'Download Test Results'
    context_dict['user_type'] = request.session['user_type']
    context_dict['school_name'] = request.session['school_name']
    school_id = request.session['school_id']

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    if request.method == 'POST':
        form = TestResultForm(request.POST, school_id=school_id)

        if form.is_valid():
            the_class = form.cleaned_data['the_class']
            section = form.cleaned_data['section']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            term = form.cleaned_data['term']
        else:
            error = 'You have missed to select either Start/End Date, or Class, or Section, or Term'
            form = TestResultForm(request.POST)
            context_dict['form'] = form
            form.errors['__all__'] = form.error_class([error])
            return render(request, 'classup/test_results.html', context_dict)

        # setup the excel file for download
        excel_file_name = 'Test_Results_' + str(the_class.standard) + '_' + str(section.section) \
                          + '_' + str(term) + '.xlsx'
        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        result_sheet = workbook.add_worksheet("Results")

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
        header2 = workbook.add_format({
            'bold': True,
            'font_size': 8,
            'bg_color': '#F7F7F7',
            'color': 'black',
            'align': 'center',
            'valign': 'top',
            'border': 1
        })
        cell_center = workbook.add_format({
            'align': 'center',
            'valign': 'top'
        })
        cell_left = workbook.add_format({
            'align': 'left',
            'valign': 'top'
        })
        low_marks = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font_color': 'red'
        })
        absent_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font_color': 'blue'
        })

        s_d = str(start_date).split('-')[2]  # start date
        s_m = str(start_date).split('-')[1]  # start month
        s_y = str(start_date).split('-')[0]  # start year
        e_d = str(end_date).split('-')[2]  # end date
        e_m = str(end_date).split('-')[1]  # end month
        e_y = str(end_date).split('-')[0]  # end year

        title_text = 'Test Result for Class ' + the_class.standard + '-' + section.section
        title_text += ' for ' + term + ' (' + s_d + '-' + s_m + '-' + s_y + ' to ' + e_d + '-' + e_m + '-' + e_y + ')'
        result_sheet.merge_range('A2:L2', title_text, title)
        result_sheet.set_column('A:A', 4)
        result_sheet.set_column('B:B', 7)
        result_sheet.set_column('C:C', 15)

        result_sheet.write(3, 0, ugettext("S No."), header)
        result_sheet.write(3, 1, ugettext("Roll No."), header)
        result_sheet.write(3, 2, ugettext("Name"), header)

        # put the subjects as header for the tests conducted in the duration
        row = 2
        col = 3
        idx = 0
        s_list = []  # list to hold Students objects
        s_list_created = False
        marks_col1 = 5
        for test in ClassTest.objects.filter(the_class=the_class, section=section,
                                             date_conducted__gte=start_date, date_conducted__lte=end_date):

            sub = test.subject.subject_name
            date_conducted = test.date_conducted
            d2 = date_conducted.strftime('%d-%m-%Y')
            # sub += ' (' + d2 + ')'
            result_sheet.merge_range(2, col, 2, col + 1, ugettext(sub), header)
            result_sheet.write(2 + 1, col, ugettext("MM"), header2)
            if not test.grade_based:
                result_sheet.write(2 + 1, col + 1, ugettext("Marks"), header2)
            else:
                result_sheet.write(2 + 1, col + 1, ugettext("Grade"), header2)
            col += 2

            if not s_list_created:
                for s in Student.objects.filter(current_class=the_class, current_section=section, active_status=True):
                    s_list.append(s)

                    result_sheet.write_number(row + 2, 0, idx + 1, cell_center)
                    result_sheet.write_number(row + 2, 1, idx + 1, cell_center)
                    result_sheet.write_string(row + 2, 2, ugettext(s.fist_name + ' ' + s.last_name), cell_left)

                    marks_col = 3

                    if not test.grade_based:
                        mm = test.max_marks
                        result_sheet.write_number(row + 2, marks_col, mm, cell_center)
                    else:
                        mm = "NA"
                        result_sheet.write(row + 2, marks_col, ugettext(mm), cell_center)
                    try:
                        result = TestResults.objects.get(class_test=test, student=s)
                        if not test.grade_based:
                            marks = result.marks_obtained
                            if marks == -1000:
                                marks = 'ABS'
                                result_sheet.write(row + 2, marks_col + 1, marks, absent_format)
                            elif marks == -5000:
                                marks = 'NA'
                                result_sheet.write(row + 2, marks_col + 1, ugettext(marks), absent_format)
                            elif marks < test.passing_marks:
                                result_sheet.write(row + 2, marks_col + 1, marks, low_marks)
                            else:
                                result_sheet.write(row + 2, marks_col + 1, marks, cell_center)
                        else:
                            grade = result.grade
                            if grade == -1000:
                                grade = 'ABS'
                                result_sheet.write(row + 2, marks_col + 1, ugettext(grade), absent_format)
                            elif grade == -5000:
                                grade = 'NA'
                                result_sheet.write(row + 2, marks_col + 1, ugettext(grade), absent_format)
                            else:
                                result_sheet.write(row + 2, marks_col + 1, ugettext(grade), cell_center)
                    except Exception as e:
                        print ('Exception occured while trying to fetch marks/grade for a student')
                        print ('Exception5 from operations views.py = %s (%s)' % (e.message, type(e)))

                    row += 1
                    idx += 1
                s_list_created = True
            else:
                print ('now dealing with=' + str(test.subject))
                row = 2
                marks_col = 5
                for s in s_list:
                    # marks_col = 5
                    if not test.grade_based:
                        mm = test.max_marks
                        result_sheet.write_number(row + 2, marks_col1, mm, cell_center)
                    else:
                        mm = "NA"
                        result_sheet.write(row + 2, marks_col1, ugettext(mm), cell_center)
                    try:
                        result = TestResults.objects.get(class_test=test, student=s)
                        if not test.grade_based:
                            marks = result.marks_obtained
                            if marks == -1000:
                                marks = 'ABS'
                                result_sheet.write(row + 2, marks_col1 + 1, marks, absent_format)
                            elif marks == -5000.00:
                                print ('No marks have been entered for this test')
                                marks = 'NA'
                                result_sheet.write(row + 2, marks_col1 + 1, marks, absent_format)
                            elif marks < test.passing_marks:
                                result_sheet.write(row + 2, marks_col1 + 1, marks, low_marks)
                            else:
                                result_sheet.write(row + 2, marks_col1 + 1, marks, cell_center)
                        else:
                            grade = result.grade
                            if grade == -1000:
                                grade = 'ABS'
                                result_sheet.write(row + 2, marks_col1 + 1, ugettext(grade), absent_format)
                            elif grade == -5000:
                                grade = 'NA'
                                result_sheet.write(row + 2, marks_col1 + 1, grade, absent_format)
                            else:
                                result_sheet.write(row + 2, marks_col1 + 1, ugettext(grade), cell_center)
                    except Exception as e:
                        print ('Exception occured while trying to fetch marks/grade for a student')
                        print ('Exception6 from operations views.py = %s (%s)' % (e.message, type(e)))
                    row += 1
                marks_col1 += 2

        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response

    if request.method == 'GET':
        form = TestResultForm(school_id=school_id)
        context_dict['form'] = form

    return render(request, 'classup/test_results.html', context_dict)


# 04/11/2017 send welcome sms to parents who have not yet downloaded the app or downloaded but never login
def send_welcome_sms(request):
    context_dict = {}
    school_id = request.session['school_id']
    school = School.objects.get(id=school_id)

    students = Student.objects.filter(school=school, active_status=True)
    student_count = 0
    message_count = 0
    for s in students:
        parent = s.parent
        mobile = parent.parent_mobile1

        # check whether this parent has ever login?
        try:
            if LoginRecord.objects.filter(login_id=mobile).exists():
                print ('parent %s with mobile %s has logged into the system before. No action required' %
                       (parent.parent_name, mobile))
            else:
                print ('parent %s with mobile %s has NEVER logged into the system before. Welcome SMS need to be send' %
                       (parent.parent_name, mobile))
                try:
                    if User.objects.filter(username=mobile).exists():
                        print('user for parent %s exist. Welcome message can be sent' % parent.parent_name)
                        try:
                            conf = Configurations.objects.get(school=school)
                            android_link = conf.google_play_link
                            iOS_link = conf.app_store_link
                            u = User.objects.get(username=mobile)
                            password = User.objects.make_random_password(length=5, allowed_chars='1234567890')
                            u.set_password(password)
                            u.save()
                            print ('password = %s ' % password)
                            message = 'Dear %s, Welcome to ClassUp' % parent.parent_name
                            message += ". Now you can track your child's progress at %s." % school.school_name
                            message += 'Your user id is: %s, and password is %s' % (str(mobile), str(password))
                            message += '. Please install ClassUp from these links. '
                            message += 'Android: %s. iOS: %s' % (android_link, iOS_link)
                            message += '. For support, email to: support@classup.in'
                            print(message)
                            message_type = 'Resend Welcome Parent'
                            sender = request.session['user']
                            sms.send_sms1(school, sender, str(mobile), message, message_type)
                            print ('sent welcom SMS to % s' % parent.parent_name)
                            message_count = message_count + 1
                            print ('now the count is %i' % message_count)
                        except Exception as e:
                            print ('failed to re-send welcome message to %s' % parent.parent_name)
                            print ('Exception 041117-B from operations views.py %s %s ' % (e.message, type(e)))
                    else:
                        print ('user for parent %s has not been created. Need to be looked into' % parent.parent_name)
                except Exception as e:
                    print ('re-send welcome SMS failed.')
                    print ('Exception 041117-C from operations views.py %s %s' % (e.message, type(e)))

        except Exception as e:
            print ('Exception 041117-A from operations views.py. %s %s' % (e.message, type(e)))
            print ('Failed to retrieve the login record for parent %s ' % parent.parent_name)
            context_dict['status'] = 'error'
            return render(request, 'classup/test_results.html', context_dict, status=201)
        student_count = student_count + 1
    print ('out of %i parents, total %i welcome messages sent for % s' %
           (student_count, message_count, school.school_name))
    context_dict['status'] = 'success'
    return render(request, 'classup/test_results.html', context_dict, status=200)


def result_sms(request):
    context_dict = {
    }
    context_dict['header'] = 'Send Term test Marks to Parents via SMS'
    context_dict['caller'] = 'result_sms'
    school_id = request.session['school_id']
    school = School.objects.get(id=school_id)
    context_dict['user_type'] = request.session['user_type']
    context_dict['school_name'] = request.session['school_name']

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    if request.method == 'POST':
        form = TestResultForm(request.POST, school_id=school_id)

        if form.is_valid():
            the_class = form.cleaned_data['the_class']
            section = form.cleaned_data['section']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            term = form.cleaned_data['term']

        else:
            print ('form could not be validated')
            error = 'You have missed to select either Start/End Date, or Class, or Section, or Term'
            form = TestResultForm(request.POST)
            context_dict['form'] = form
            form.errors['__all__'] = form.error_class([error])
            return render(request, 'classup/test_results.html', context_dict)

        try:
            for s in Student.objects.filter(current_class=the_class, current_section=section, active_status=True):
                the_name = s.fist_name
                if ' ' in s.fist_name:
                    (f_name, l_name) = the_name.split(' ')
                else:
                    f_name = the_name
                the_name = f_name
                message = 'Dear ' + s.parent.parent_name + ', subject-wise marks of your ward, '

                message += ugettext(the_name)
                message += ', for ' + term + ' test: '
                try:
                    for test in ClassTest.objects.filter(the_class=the_class, section=section,
                                                         date_conducted__gte=start_date,
                                                         date_conducted__lte=end_date):
                        message += test.subject.subject_name + ' = '
                        if not test.grade_based:
                            mm = int(test.max_marks)
                            try:
                                tr = TestResults.objects.get(class_test=test, student=s)
                                marks = float(tr.marks_obtained)
                                if marks.is_integer():
                                    marks = int(marks)
                                else:
                                    marks = round(marks, 1)
                                if marks == -1000:
                                    marks = 'ABS'
                                message += str(marks) + '/' + str(mm) + ', '
                            except Exception as e:
                                print ('error occured while fetching marks for ' +
                                       str(s) + ' for test.subject.subject_name')
                                print ('Exception7 from operations views.py = %s (%s)' % (e.message, type(e)))
                        else:
                            try:
                                tr = TestResults.objects.get(class_test=test, student=s)
                                grade = tr.grade
                                if grade == -1000:
                                    grade = 'ABS'
                                message += str(grade) + '(Grade) '
                            except Exception as e:
                                print ('error occured while fetching grade for ' +
                                       str(s) + ' for test.subject.subject_name')
                                print ('Exception8 from operations views.py = %s (%s)' % (e.message, type(e)))
                except Exception as e:
                    print ('error occured while fetching the list of tests')
                    print ('Exception9 from operations views.py = %s (%s)' % (e.message, type(e)))
                message += ' Regards, ' + school.school_name
                print(message)
                message_type = 'Term Test Subject Wise Marks'
                sender = request.session['user']
                p = s.parent
                m1 = p.parent_mobile1

                sms.send_sms1(school, sender, m1, message, message_type)

                configuration = Configurations.objects.get(school=school)
                if configuration.send_absence_sms_both_to_parent:
                    m2 = p.parent_mobile2
                    if m2 != '':
                        sms.send_sms1(school, sender, m2, message, message_type)
        except Exception as e:
            print ('error occured while fetching the list of students')
            print ('Exception10 from operations views.py = %s (%s)' % (e.message, type(e)))
        return render(request, 'classup/setup_index.html', context_dict)

    if request.method == 'GET':
        form = TestResultForm(school_id=school_id)
        context_dict['form'] = form

    return render(request, 'classup/test_results.html', context_dict)


class ParentCommunicationReport(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    context_dict = {'header': 'Parent Communication Report'}

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        print(data)
        school_id = data['school_id']
        school = School.objects.get(pk=school_id)
        school_name = school.school_name

        the_date = data['date']

        m = the_date.split('-')[1]
        month_int = int(m)
        print('month_int = %d' % month_int)
        month = calendar.month_name[month_int]
        y = the_date.split('-')[0]
        year_int = int(y)
        print('year_int = %d' % year_int)

        excel_file_name = 'Parents_Communication' + '_' + str(month) + '_' + str(y) + '.xlsx'

        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        main_sheet = workbook.add_worksheet("Communication from Parents")

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
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yy'
        })

        title_text = 'Parents Communications  ' + 'for ' + month + '/' + y
        main_sheet.merge_range('A2:F2', title_text, title)

        main_sheet.set_column('A:A', 4)
        main_sheet.set_column('B:B', 10)
        main_sheet.set_column('C:C', 20)
        main_sheet.set_column('D:D', 15)
        main_sheet.set_column('E:E', 15)
        main_sheet.set_column('F:F', 15)
        main_sheet.set_column('G:G', 15)
        main_sheet.set_column('H:H', 20)
        main_sheet.set_column('I:I', 50)

        current_row = 3
        main_sheet.write(current_row, 0, ugettext("S No."), header)
        main_sheet.write(current_row, 1, ugettext("Date"), header)
        main_sheet.write(current_row, 2, ugettext("Parent Name"), header)
        main_sheet.write(current_row, 3, ugettext("Mobile"), header)
        main_sheet.write(current_row, 4, ugettext("Student Name"), header)
        main_sheet.write(current_row, 5, ugettext("Class"), header)
        main_sheet.write(current_row, 6, ugettext("Class Teacher"), header)
        main_sheet.write(current_row, 7, ugettext("Category"), header)
        main_sheet.write(current_row, 8, ugettext("Communication"), header)

        communications = ParentCommunication.objects.filter(student__school=school, date_sent__month=month_int,
                                                            date_sent__year=year_int).order_by('-date_sent')
        sr_no = 1
        for c in communications:
            current_row += 1
            main_sheet.write_number(current_row, 0, sr_no)

            # get the date on which the parent sent the communication
            communication_date = c.date_sent
            main_sheet.write(current_row, 1, communication_date, date_format)

            # get the parent name
            parent_name = c.student.parent.parent_name
            main_sheet.write(current_row, 2, ugettext(parent_name))

            # get the parent mobile
            parent_mobile = c.student.parent.parent_mobile1
            main_sheet.write(current_row, 3, ugettext(parent_mobile))

            # get the student name
            student_name = c.student.fist_name + ' ' + c.student.last_name
            main_sheet.write(current_row, 4, ugettext(student_name))

            # ge the student class/section
            student_class = c.student.current_class.standard + '-' + c.student.current_section.section
            main_sheet.write(current_row, 5, ugettext(student_class))

            # get the class teacher name
            try:
                ct = ClassTeacher.objects.get(standard=c.student.current_class, section=c.student.current_section)
                teacher_name = ct.class_teacher.first_name + ' ' + ct.class_teacher.last_name
            except Exception as e:
                print ('Class Teacher not set for ' + student_class)
                print ('Exception14 from operations views.py = %s (%s)' % (e.message, type(e)))
                teacher_name = "N/A"

            main_sheet.write(current_row, 6, ugettext(teacher_name))

            # get the category
            category = c.category.category
            main_sheet.write(current_row, 7, ugettext(category))

            # get the message
            message = c.communication_text
            main_sheet.write(current_row, 8, ugettext(message))

            sr_no += 1

        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response

