from datetime import datetime, date
import calendar
from calendar import monthrange
import StringIO

import os
import json
from django.core.servers.basehttp import FileWrapper

import xlsxwriter

from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.contrib import messages
import mimetypes
from django.core.urlresolvers import reverse
from authentication.views import JSONResponse

from .forms import SchoolAttSummaryForm, AttendanceRegisterForm
from .forms import TestResultForm, ParentsCommunicationDetailsForm, BulkSMSForm
import sms

from academics.models import Class, Section, Subject, ClassTest, TestResults, ClassTeacher
from student.models import Student
from teacher.models import Teacher
from attendance.models import Attendance, AttendanceTaken
from parents.models import  ParentCommunication
from setup.models import Configurations, School

# Create your views here.


def operations_index(request):
    pass


def att_summary_school(request):
    context_dict = {
    }
    context_dict['header'] = 'Daily Class-wise Attendance Summary'

    # first see whether the cancel button was pressed
    if "cancel" in request.GET:
        return HttpResponseRedirect(reverse('setup_index'))

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
        cell_center = workbook.add_format({
            'align': 'center',
            'valign': 'top'
        })
        cell_left = workbook.add_format({
            'align': 'left',
            'valign': 'top'
        })
        perc_format = workbook.add_format({
            'num_format': '0.00%',
            'align': 'center'
        })
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
        for c in Class.objects.all():
            for s in Section.objects.all():
                total = Student.objects.filter(current_class=c, current_section=s).count()
                grand_total += total
                row = 3 + idx

                if 0 != total:
                    # check whether attendance for this class/section has been taken yet or not?
                    att_taken = AttendanceTaken.objects.filter(date=converted_date, the_class=c,
                                                               section=s, subject=main).count()
                    if 0 == att_taken:
                        summary_sheet.write_number(row, 0, idx+1, cell_center)
                        summary_sheet.write_string(row, 1, c.standard, cell_center)
                        summary_sheet.write_string(row, 2, s.section, cell_center)
                        summary_sheet.write_number(row, 3, total, cell_center)
                        merge_range = 'E' + str(row+1) + ':' + 'G' + str(row+1)
                        summary_sheet.merge_range(merge_range, "Attendance Not Taken", summary_row)
                        idx += 1
                        continue

                    absent = Attendance.objects.filter(date=converted_date,
                                                       the_class=c, section=s, subject=main).count()
                    present = total - absent
                    perc_present = float(float(present)/float(total))

                    #grand_total += total
                    p_total += present
                    a_total += absent
                    grand_present_perc = float(float(p_total)/float(grand_total))



                    summary_sheet.write_number(row, 0, idx+1, cell_center)
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
            merge_range = 'A' + str(row+1) + ':' 'C' + str(row+1)
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


def att_register_class(request):
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return HttpResponseRedirect(reverse('setup_index'))

    context_dict = {
    }
    context_dict['header'] = 'Download Monthly Attendance'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)
        form = AttendanceRegisterForm(request.POST, school_id=school_id)

        if form.is_valid():
            the_class = form.cleaned_data['the_class']
            section = form.cleaned_data['section']
            the_subject = form.cleaned_data['subject']
            the_date = form.cleaned_data['date']

        else:
            error = 'You have missed to select either Date, or Class, or Section, or Subject'
            form = AttendanceRegisterForm(request)
            context_dict['form'] = form
            form.errors['__all__'] = form.error_class([error])
            return render(request, 'classup/att_register.html', context_dict)

        m = the_date.split('-')[1]
        month_int = int(m)
        month = calendar.month_name[month_int]
        y = the_date.split('-')[0]
        year_int = int(y)

        excel_file_name = 'Attendance_Resigter_' + str(the_class.standard) + '_' + str(section.section)
        excel_file_name += '_' + str(the_subject) + '_' + str(month) + '_' + str(y) + '.xlsx'

        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        attendance_sheet = workbook.add_worksheet("Attendance")

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
        cell_center = workbook.add_format({
            'align': 'center',
            'valign': 'top'
        })
        cell_left = workbook.add_format({
            'align': 'left',
            'valign': 'top'
        })
        present_format = workbook.add_format({
            'align': 'center',
            'valign': 'top',
            'font_color': 'green'
        })
        absent_format = workbook.add_format({
            'align': 'center',
            'valign': 'top',
            'font_color': '#FF0000'
        })
        holiday_format = workbook.add_format({
            'align': 'center',
            'valign': 'top',
            'font_color': 'blue'
        })
        perc_format = workbook.add_format({
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'top'
        })

        title_text = 'Monthly Attendance for Class ' + the_class.standard + '-' + section.section +\
                     ', Subject: ' + str(the_subject)
        title_text += ' for ' + month + '/' + y
        attendance_sheet.merge_range('A2:Q2', title_text, title)
        attendance_sheet.set_column('A:A', 4)
        attendance_sheet.set_column('B:B', 7)
        attendance_sheet.set_column('C:C', 15)
        attendance_sheet.set_column('D:AG', 3)
        attendance_sheet.set_column('AH:AI', 5)

        attendance_sheet.write(3, 0, ugettext("S No."), header)
        attendance_sheet.write(3, 1, ugettext("Roll No."), header)
        attendance_sheet.write(3, 2, ugettext("Name"), header)

        # Next 28/29/30/31 columns will be for dates. We need to get the number fo days in the month
        DayL = ['M', 'Tu', 'W', 'Th', 'F', 'Sa', 'Su']

        days = monthrange(year_int, month_int)[1]
        for d in range(1, days+1):
            date_for_db = date(year_int, month_int, int(d))
            the_day = DayL[date_for_db.weekday()]

            attendance_sheet.write(2, d+2, ugettext(the_day), header)
            attendance_sheet.write_number(3, d+2, d, header)
        attendance_sheet.write(3, days+3, ugettext("Total"), header)
        attendance_sheet.write(3, days+4, ugettext("%"), header)
        attendance_sheet.write(3, days+5, ugettext("Till Date"), header)
        attendance_sheet.write(3, days+6, ugettext("Till Date %"), header)

        idx = 0
        row = 4 + idx

        # 04/08/2016 - Changed functionality to retrieve attendance for a specific subject. Done for coaching/college
        #subject = Subject.objects.get(subject_name='Main')
        subject = Subject.objects.get(school=school, subject_name=the_subject)

        # we will cache the list of holidays so that the execution is faster, and less hits to db means
        # saving on AWS bill!
        holidays = []

        holiday_count = present_count = 0
        db_hit = 1
        for s in Student.objects.filter(school=school, current_class=the_class, current_section=section):
            attendance_sheet.write_number(row, 0, idx+1, cell_center)
            attendance_sheet.write_number(row, 1, s.roll_number, cell_center)
            attendance_sheet.write_string(row, 2, ugettext(s.fist_name + ' ' + s.last_name), cell_left)

            db_hit += 1
            for d in range(1, days+1):
                date_for_db = date(year_int, month_int, int(d))
                if d not in holidays:
                    try:
                        a = AttendanceTaken.objects.filter(date=date_for_db,
                                                           the_class=the_class, section=section, subject=subject)
                        db_hit += 1
                        if 0 < a.count():   # this means this date was not a holiday :( and attendance was taken
                            # check if this student was present in the class that day or was in a cinema hall or mall :)
                            try:
                                q = Attendance.objects.filter(date=date_for_db, student=s,
                                                              the_class=the_class, section=section, subject=subject)
                                db_hit += 1
                                if 0 < q.count():    # student bunked this class!
                                    attendance_sheet.write_string(row, d+2, ugettext("A"), absent_format)
                                else:   # student was getting bored attending this lecture
                                    attendance_sheet.write_string(row, d+2, ugettext("P"), present_format)
                                    present_count += 1
                            except Exception as e:
                                print ('exception occured while doing lookup in the Attendance table')
                                print ('Exception = %s (%s)' % (e.message, type(e)))
                        else:   # wow, this day was a holiday
                            holidays.append(d)
                            holiday_count += 1
                            attendance_sheet.write(row, d+2, ugettext("NA"), holiday_format)

                    except Exception as e:
                        print ('exception occured while doing lookup in the AttendanceTaken table')
                        print ('Exception = %s (%s)' % (e.message, type(e)))
                else:
                    attendance_sheet.write(row, d+2, ugettext("NA"), holiday_format)

                working_days = days - holiday_count
                attendance_sheet.write_string(row, d+3,
                                              ugettext(str(present_count) + '/' + str(working_days)), cell_center)
                try:
                    perc_present = float(float(present_count)/float(working_days))
                    attendance_sheet.write_number(row, d+4, perc_present, perc_format)
                except Exception as e:
                    print ('exception occured while trying to calculate percentage')
                    print ('Exception = %s (%s)' % (e.message, type(e)))

            # calculate the till date attendance for this student
            try:
                conf = Configurations.objects.get(school=school)
                session_start_month = conf.session_start_month
                if month_int < session_start_month:
                    start = date(year_int-1, session_start_month, 1)
                else:
                    start = date(year_int, session_start_month, 1)
                no_of_days = calendar.monthrange(year_int, month_int)[1]
                end = date (year_int, month_int, no_of_days)

                q = AttendanceTaken.objects.filter(the_class=the_class, section=section,
                                                   subject=subject, date__range=[start, end])
                working_days_till_date = q.count()

                #q = Attendance.objects.filter(student=s, date__range=[start, end])
                q = Attendance.objects.filter(student=s, subject=subject, date__range=[start, end])
                absent_days_till_date = q.count()

                present_days_till_date = working_days_till_date - absent_days_till_date
                attendance_sheet.write(row, d+5,
                                       ugettext(str(present_days_till_date) + '/' + str(working_days_till_date)),
                                       cell_center)
                if int(working_days_till_date) < 1:
                    present_perc_till_date = 'N/A'
                    attendance_sheet.write_string(row, d+6, present_perc_till_date)
                else:
                    present_perc_till_date = float(float(present_days_till_date)/float(working_days_till_date))
                    attendance_sheet.write(row, d+6, present_perc_till_date, perc_format)
            except Exception as e:
                print ('unable to calculate attendance till date')
                print ('Exception = %s (%s)' % (e.message, type(e)))

            row += 1
            idx += 1
            present_count = 0

        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response

    if request.method == 'GET':
        school_id = request.session['school_id']
        form = AttendanceRegisterForm(school_id=school_id)
        context_dict['form'] = form

    return render(request, 'classup/att_register.html', context_dict)


def send_bulk_sms(request):
    context_dict = {
    }
    context_dict['header'] = 'Send Bulk SMS'
    context_dict['user_type'] = 'school_admin'
    school_id = request.session['school_id']
    school = School.objects.get(id=school_id)

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    if request.method == 'POST':
        form = BulkSMSForm(request.POST, school_id=school_id)
        context_dict['form'] = form

        message_body = request.POST['message_text']
        if message_body == '':
            error = 'Message is Empty'
            form.errors['__all__'] = form.error_class([error])
            print (error)
            return render(request, 'classup/bulk_sms.html', context_dict)

        selected_classes = request.POST.getlist('Class')
        staff = request.POST.getlist('Staff')
        print(staff)
        if len(selected_classes) == 0 and len(staff) == 0:
            error = 'You have not selected any Class, Teacher, or Staff'
            form.errors['__all__'] = form.error_class([error])
            print (error)
            return render(request, 'classup/bulk_sms.html', context_dict)

        for sc in selected_classes:
            the_class = Class.objects.get(school=school, standard=sc)
            print(the_class.standard)
            student_list = Student.objects.filter(current_class=the_class)
            for student in student_list:
                print(student.fist_name + ' ' + student.last_name)
                parent = student.parent
                print(parent)
                message = 'Dear Ms/Mr. ' + parent.parent_name + ', '
                message += message_body + ' Regards, ' + school.school_name
                print(message)
                mobile = parent.parent_mobile1
                print(mobile)
                sms.send_sms(mobile, message)

        for st in staff:
            if st == 'teacher':
                for teacher in Teacher.objects.all():
                    teacher_name = teacher.first_name + ' ' + teacher.last_name
                    print(teacher_name)
                    message = 'Dear Ms/Mr. ' + teacher_name + ', '
                    message += message_body + ' Regards, ' + school.school_name
                    print(message)
                    teacher_mobile = teacher.mobile
                    print(teacher_mobile)
                    sms.send_sms(teacher_mobile, message)

        context_dict['header'] = 'Operation Completed'
        messages.success(request, 'Messages Sent!')
        return render(request, 'classup/setup_index.html', context_dict)

    if request.method == 'GET':
        print('getting the bulk sms form')
        form = BulkSMSForm(school_id=school_id)
        context_dict['form'] = form

    return render(request, 'classup/bulk_sms.html', context_dict)


def test_result(request):
    context_dict = {
    }
    context_dict['header'] = 'Download Test Results'
    school_id = request.session['school_id']

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return HttpResponseRedirect(reverse('setup_index'))

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
        e_d = str(end_date).split('-')[2]    # end date
        e_m = str(end_date).split('-')[1]    # end month
        e_y = str(end_date).split('-')[0]    # end year

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
        s_list = []         # list to hold Students objects
        s_list_created = False
        marks_col1 = 5
        for test in ClassTest.objects.filter(the_class=the_class, section=section,
                                             date_conducted__gte=start_date, date_conducted__lte=end_date):

            sub = test.subject.subject_name
            date_conducted = test.date_conducted
            d2 = date_conducted.strftime('%d-%m-%Y')
            sub += ' (' + d2 + ')'
            result_sheet.merge_range(2, col, 2, col+1, ugettext(sub), header)
            result_sheet.write(2+1, col, ugettext("MM"), header2)
            if not test.grade_based:
                result_sheet.write(2+1, col+1, ugettext("Marks"), header2)
            else:
                result_sheet.write(2+1, col+1, ugettext("Grade"), header2)
            col += 2

            if not s_list_created:
                for s in Student.objects.filter(current_class=the_class, current_section=section):
                    s_list.append(s)

                    result_sheet.write_number(row+2, 0, idx+1, cell_center)
                    result_sheet.write_number(row+2, 1, s.roll_number, cell_center)
                    result_sheet.write_string(row+2, 2, ugettext(s.fist_name + ' ' + s.last_name), cell_left)

                    marks_col = 3

                    if not test.grade_based:
                        mm = test.max_marks
                        result_sheet.write_number(row+2, marks_col, mm, cell_center)
                    else:
                        mm = "NA"
                        result_sheet.write(row+2, marks_col, ugettext(mm), cell_center)
                    try:
                        result = TestResults.objects.get(class_test=test, student=s)
                        if not test.grade_based:
                            marks = result.marks_obtained
                            if marks == -1000:
                                marks = 'ABS'
                                result_sheet.write(row+2, marks_col+1, marks, absent_format)
                            elif marks == -5000:
                                marks = 'NA'
                                result_sheet.write(row+2, marks_col+1, ugettext(marks), absent_format)
                            elif marks < test.passing_marks:
                                result_sheet.write(row+2, marks_col+1, marks, low_marks)
                            else:
                                result_sheet.write(row+2, marks_col+1, marks, cell_center)
                        else:
                            grade = result.grade
                            if grade == -1000:
                                grade = 'ABS'
                                result_sheet.write(row+2, marks_col+1, ugettext(grade), absent_format)
                            elif grade == -5000:
                                grade = 'NA'
                                result_sheet.write(row+2, marks_col+1, ugettext(grade), absent_format)
                            else:
                                result_sheet.write(row+2, marks_col+1, ugettext(grade), cell_center)
                    except Exception as e:
                        print ('Exception occured while trying to fetch marks/grade for a student')
                        print ('Exception = %s (%s)' % (e.message, type(e)))

                    row += 1
                    idx += 1
                s_list_created = True
            else:
                print ('now dealing with=' + str(test.subject))
                row = 2
                marks_col = 5
                for s in s_list:
                    #marks_col = 5
                    if not test.grade_based:
                        mm = test.max_marks
                        result_sheet.write_number(row+2, marks_col1, mm, cell_center)
                    else:
                        mm = "NA"
                        result_sheet.write(row+2, marks_col1, ugettext(mm), cell_center)
                    try:
                        result = TestResults.objects.get(class_test=test, student=s)
                        if not test.grade_based:
                            marks = result.marks_obtained
                            if marks == -1000:
                                marks = 'ABS'
                                result_sheet.write(row+2, marks_col1+1, marks, absent_format)
                            elif marks == -5000.00:
                                print ('No marks have been entered for this test')
                                marks = 'NA'
                                result_sheet.write(row+2, marks_col1+1, marks, absent_format)
                            elif marks < test.passing_marks:
                                result_sheet.write(row+2, marks_col1+1, marks, low_marks)
                            else:
                                result_sheet.write(row+2, marks_col1+1, marks, cell_center)
                        else:
                            grade = result.grade
                            if grade == -1000:
                                grade = 'ABS'
                                result_sheet.write(row+2, marks_col1+1, ugettext(grade), absent_format)
                            elif grade == -5000:
                                grade = 'NA'
                                result_sheet.write(row+2, marks_col1+1, grade, absent_format)
                            else:
                                result_sheet.write(row+2, marks_col1+1, ugettext(grade), cell_center)
                    except Exception as e:
                        print ('Exception occured while trying to fetch marks/grade for a student')
                        print ('Exception = %s (%s)' % (e.message, type(e)))
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


def result_sms(request):
    context_dict = {
    }
    context_dict['header'] = 'Send Term test Marks to Parents via SMS'
    context_dict['caller'] = 'result_sms'
    school_id = request.session['school_id']
    school = School.objects.get(id=school_id)
    conf = Configurations.objects.get(school=school)

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return HttpResponseRedirect(reverse('setup_index'))

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
            for s in Student.objects.filter(current_class=the_class, current_section=section):
                message = 'Dear Ms/Mr ' + s.parent.parent_name + ', please find subject-wise marks of your ward, '
                message += ugettext(s.fist_name + ' ' + s.last_name)
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
                                print ('Exception = %s (%s)' % (e.message, type(e)))
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
                                print ('Exception = %s (%s)' % (e.message, type(e)))

                except Exception as e:
                    print ('error occured while fetching the list of tests')
                    print ('Exception = %s (%s)' % (e.message, type(e)))
                message += ' Regards, ' + school.school_name
                print(message)
                p = s.parent
                m1 = p.parent_mobile1
                m2 = p.parent_mobile2

                # 11/20 - we may need to send sms for about 40-50 students, which can be time consumeing.
                # Hence we use thread
                # thread1 = Thread(target=sms.send_sms, args=(m1, message))
                # thread1.start()
                sms.send_sms(m1, message)

                if m2 != '':
                    # thread2 = Thread(target=sms.send_sms, args=(m2, message))
                    # thread2.start()
                    sms.send_sms(m2, message)
        except Exception as e:
            print ('error occured while fetching the list of students')
            print ('Exception = %s (%s)' % (e.message, type(e)))
        return render(request, 'classup/setup_index.html', context_dict)

    if request.method == 'GET':
        form = TestResultForm(school_id=school_id)
        context_dict['form'] = form

    return render(request, 'classup/test_results.html', context_dict)


@csrf_exempt
def send_message(request, school_id):
    if request.method == 'POST':
        response = {

        }
        try:
            school = School.objects.get(id=school_id)
            data = json.loads(request.body)
            message_content = data['message']
            email = data['teacher']
            t = Teacher.objects.get(email=email)
            teacher_name = t.first_name + ' ' + t.last_name
            # configuration = Configurations.objects.get(school=school)
            school_name = school.school_name
            message_trailer = '. Regards, ' + teacher_name + ', ' + school_name

            # check if the message is to be sent to all the parents
            if data["whole_class"] == "true":
                the_class = data["class"]
                c = Class.objects.get(school=school, standard=the_class)
                the_section = data["section"]
                sec = Section.objects.get(school=school, section=the_section)

                # get the list of all students in this class/section
                try:
                    student_list = Student.objects.filter(current_class=c, current_section=sec)
                    for s in student_list:
                        p = s.parent
                        m1 = p.parent_mobile1
                        m2 = p.parent_mobile2

                        message_header = 'Dear Ms/Mr ' + p.parent_name + ', this is message regarding your ward ' + \
                                         s.fist_name + ' ' + s.last_name + ': '
                        message = message_header + message_content + message_trailer
                        print (message)

                        sms.send_sms(m1, message)

                        if m2 != '':
                            sms.send_sms(m2, message)
                except Exception as e:
                    print ('Unable to send message while trying for whole class')
                    print ('Exception = %s (%s)' % (e.message, type(e)))
                response["status"] = "success"

            # the message is to be sent to parents of selected students only
            else:
                for key in data:
                    if (key != 'message') and (key != 'teacher') and (key != 'whole_class'):
                        student_id = data[key]

                        s = Student.objects.get(pk=student_id)
                        p = s.parent
                        m1 = p.parent_mobile1
                        print (m1)
                        m2 = p.parent_mobile2
                        print (m2)

                        message_header = 'Dear Ms/Mr ' + p.parent_name + ', this is message regarding your ward ' + \
                                             s.fist_name + ' ' + s.last_name + ': '
                        message = message_header + message_content + message_trailer
                        print ('message=' + message)
                        try:
                            sms.send_sms(m1, message)
                        except Exception as e:
                            print ('Unable to send message to ' + p.parent_name + 'with mobile number: ' + m1)
                            print ('Exception = %s (%s)' % (e.message, type(e)))

                        if m2 != '':
                            try:
                                sms.send_sms(m2, message)
                            except Exception as e:
                                print ('Unable to send message to ' + p.parent_name + 'with mobile number: ' + m2)
                                print ('Exception = %s (%s)' % (e.message, type(e)))

                response["status"] = "success"
        except Exception as e:
            print ('Unable to send message')
            print ('Exception = %s (%s)' % (e.message, type(e)))

    return JSONResponse(response, status=200)


def parents_communication_details(request):
    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return HttpResponseRedirect(reverse('setup_index'))

    context_dict = {
    }
    context_dict['header'] = 'Download Parents Communications'
    if request.method == 'POST':
        form = ParentsCommunicationDetailsForm(request.POST)

        if form.is_valid():
            the_date = form.cleaned_data['date']
        else:
            print ('form could not be validated')
            error = 'You have missed to select the Month/Year'
            form = ParentsCommunicationDetailsForm()
            context_dict['form'] = form
            form.errors['__all__'] = form.error_class([error])
            return render(request, 'classup/parents_communication_details.html', context_dict)

        m = the_date.split('-')[1]
        month_int = int(m)
        month = calendar.month_name[month_int]
        y = the_date.split('-')[0]
        year_int = int(y)

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
        main_sheet.write(current_row, 8, ugettext("Comminication"), header)

        communications = ParentCommunication.objects.filter(date_sent__month=month_int, date_sent__year=year_int)
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
                print ('Exception = %s (%s)' % (e.message, type(e)))
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

    if request.method == 'GET':
        form = ParentsCommunicationDetailsForm()
        context_dict['form'] = form

    return render(request, 'classup/parents_communication_details.html', context_dict)


def download_android(request):
    the_file = '/download/android/ClassUp-release.apk'
    filename = os.path.basename(the_file)

    chunk_size = 8192
    response = StreamingHttpResponse(FileWrapper(open(the_file), chunk_size),
                           content_type='file')
    response['Content-Length'] = os.path.getsize(the_file)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response


def download_ios(request):
    the_file = '/download/android/ClassUp-release.apk'
    filename = os.path.basename(the_file)
    chunk_size = 8192
    response = StreamingHttpResponse(FileWrapper(open(the_file), chunk_size),
                           content_type=mimetypes.guess_type(the_file)[0])
    response['Content-Length'] = os.path.getsize(the_file)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response
