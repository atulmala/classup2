
import requests

from PIL import Image

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import xlrd
import xlsxwriter
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell
import StringIO

from setup.models import Configurations
from setup.forms import ExcelFileUploadForm
from setup.models import School
from setup.views import validate_excel_extension

from student.models import Student, DOB, AdditionalDetails
from academics.models import Class, Section, Subject, ThirdLang, ClassTest, \
    Exam, TermTestResult, TestResults, CoScholastics, ClassTeacher

from .models import Scheme, HigherClassMapping, NPromoted
from .forms import TermResultForm, ResultSheetForm


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


def setup_scheme(request):
    context_dict = {'user_type': 'school_admin', 'school_name': request.session['school_name']}

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Setup Scheme'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for scheme setup...')
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
                    standard = sheet.cell(row, 0).value
                    print(standard)
                    try:
                        the_class = Class.objects.get(school=school, standard=standard)
                        print ('now dealing with class %s of %s' % (standard, school.school_name))
                    except Exception as e:
                        print ('exception 011117-A from exam views.py %s %s ' % (e.message, type(e)))
                        continue

                    for col in range(1, 9):
                        sub = sheet.cell(row, col).value
                        print(sub)
                        if sub == 'N/A':
                            continue

                        try:
                            subject = Subject.objects.get(school=school, subject_name=sub)
                        except Exception as e:
                            print ('exception 011117-B from exam views.py %s %s ' % (e.message, type(e)))
                            continue

                        sequence = col
                        try:
                            scheme = Scheme.objects.get(school=school, the_class=the_class, subject=subject)
                            print('subject %s in the scheme of class %s of school %s already exist. '
                                  'This will be updated' % (sub, standard, school.school_name))
                            scheme.sequence = sequence
                            scheme.subject = subject
                            try:
                                scheme.save()
                                print ('successfully updated the scheme of subject %s of class %s of school %s' %
                                       (sub, standard, school.school_name))
                            except Exception as e:
                                print ('failed to updated the scheme of subject %s of class %s of school %s' %
                                       (sub, standard, school.school_name))
                                print('exception 021117-B exam views.py %s %s ' % (e.message, type(e)))
                        except Exception as e:
                            print('scheme of subject %s of class %s of school %s is not set yet. This will be created' %
                                  (sub, standard, school.school_name))
                            print('exception 201117-C from exam views.py %s %s'% (e.message, type(e)))
                            try:
                                scheme = Scheme(school=school, the_class=the_class, sequence=sequence, subject=subject)
                                scheme.save()
                                print ('successfully created the scheme of subject %s of class %s of school %s' %
                                       (sub, standard, school.school_name))
                            except Exception as e:
                                print ('failed in creating the scheme of subject %s of class %s of school %s'%
                                       (sub, standard, school.school_name))
                                print ('exception 021117-D from exam views.py %s %s' % (e.message, type(e)))

                # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Scheme successfully uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 021117-E from exam views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_higher_class_subject_mapping(request):
    context_dict = {'user_type': 'school_admin', 'school_name': request.session['school_name']}

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    context_dict['header'] = 'Subject Mapping for Higher Classes'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)
        print (school)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for Higher classes subject mapping...')
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
                    # get the subject name
                    if row == 0:
                        sub = sheet.cell(row, 1).value
                        try:
                            subject = Subject.objects.get (school=school, subject_name=sub)
                            continue
                        except Exception as e:
                            print ('exception 141117-E from exam views.py %s %s' % (e.message, type(e)))
                            error = 'failed to retrieve subject for %s ' % sub
                            print (error)
                            form.errors['__all__'] = form.error_class([error])
                            return render(request, 'classup/setup_data.html', context_dict)
                    else:
                        partial_erp = str(sheet.cell(row, 0).value)
                        student_name = sheet.cell(row, 1).value
                        try:
                            students = Student.objects.filter(school=school, student_erp_id__contains=partial_erp)
                            for s in students:
                                print ('full erp = %s' % s.student_erp_id)
                                try:
                                    mapping = HigherClassMapping.objects.get(student=s, subject=subject)
                                    print (mapping)
                                    print ('subject %s mapping for %s already exist. Not doing again.'
                                           % (sub, student_name))
                                except Exception as e:
                                    print ('exception 141117-C from exam views.py %s %s' % (e.message, type(e)))
                                    print ('subject %s mapping for %s does not exist. Hence creating...'
                                           % (sub, student_name))
                                    try:
                                        mapping = HigherClassMapping(student=s, subject=subject)
                                        mapping.save()
                                        print ('created %s subject mapping for % s' % (sub, student_name))
                                    except Exception as e:
                                        print ('exception 141117-D from exam views.py %s %s' % (e.message, type(e)))
                                        print ('failed to create %s subject mapping for % s' % (sub, student_name))
                        except Exception as e:
                            print ('failed to create %s subject mapping for %s ' % (sub, student_name))
                            print ('exception 141117-A from exam views.py %s %s' % (e.message, type(e)))
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 141117-B from exam views.py %s %s' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def setup_third_lang(request):
    context_dict = {
    }
    context_dict['user_type'] = 'school_admin'
    context_dict['school_name'] = request.session['school_name']

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    # now start processing the file upload

    context_dict['header'] = 'Setup Third Language'
    if request.method == 'POST':
        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for Third Language mapping...')
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
                        print ('exception 231017-G from exam views.py %s %s ' % (e.message, type(e)))
                        continue

                    # 31/10/2017 - get the third language
                    t_l = sheet.cell(row, 2).value
                    try:
                        third_lang = Subject.objects.get(school=school, subject_name=t_l)
                    except Exception as e:
                        print('Exception 311017-A from exam views.py %s %s' % (e.message, type(e)))
                        print('%s is not a third languate!' % t_l)

                    try:
                        record = ThirdLang.objects.get(student=student)
                        print ('third language ' + student.fist_name + ' ' +
                               student.last_name + ' already exists. This will be updated')
                        try:
                            record.third_lang = third_lang
                            record.save()
                            print ('successfully updated the third language for ' +
                                   student.fist_name, ' ' + student.last_name)
                        except Exception as e:
                            print ('failed to update the third language for '+
                                   student.fist_name, ' ' + student.last_name)
                            print ('(exception 311017-B from exam views.py %s %s) ' % (e.message, type(e)))
                    except Exception as e:
                        print ('(exception 311017-C from exam views.py %s %s) ' % (e.message, type(e)))
                        print ('third language for ' + student.fist_name + ' ' +
                               student.last_name + ' is not in record. This will be created')
                        try:
                            new_record = ThirdLang(student=student, third_lang=third_lang)
                            new_record.save()
                            print (('created third language entry for %s %s)' %
                                    (student.fist_name, student.last_name)))
                        except Exception as e:
                            print ('failed to create third language entry for %s %s)' %
                                   (student.fist_name, student.last_name))
                            print ('(exception 311017-D from exam views.py %s %s) ' % (e.message, type(e)))

                            # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request, 'Third Language uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 311017-E from exam views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)
    else:
        form = ExcelFileUploadForm()
        context_dict['form'] = form
    return render(request, 'classup/setup_data.html', context_dict)


def term_results(request):
    context_dict = {

    }
    # first see whether the cancel button was pressed
    context_dict['school_name'] = request.session['school_name']

    if request.session['user_type'] == 'school_admin':
        context_dict['user_type'] = 'school_admin'

    # first see whether the cancel button was pressed
    if "cancel" in request.POST:
        return render(request, 'classup/setup_index.html', context_dict)

    context_dict['header'] = 'Term Results'
    if request.method == 'POST':
        school_id = request.session['school_id']
        print(school_id)
        school = School.objects.get(id=school_id)
        print(school)
        print('yes, the request method is post!')

        form = TermResultForm(request.POST, school_id=school_id)

        if form.is_valid():
            print('form is valid')
            the_class = form.cleaned_data['the_class']
            print(the_class)
            section = form.cleaned_data['section']
            print(section)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'
            return response
        else:
            error = 'You have missed to select either Class, or Section'
            form = TermResultForm(request)
            context_dict['form'] = form
            form.errors['__all__'] = form.error_class([error])
            return render(request, 'classup/term_result.html', context_dict)

    if request.method == 'GET':
        print('form method is get')
        school_id = request.session['school_id']
        form = TermResultForm(school_id=school_id)
        context_dict['form'] = form

    return render(request, 'classup/term_result.html', context_dict)


def get_grade(marks):
    if 100 >= marks > 90:
        grade = 'A1'
        return grade
    if 90 >= marks > 80:
        grade = 'A2'
        return grade
    if 80 >= marks > 70:
        grade = 'B1'
        return grade
    if 70 >= marks > 60:
        grade = 'B2'
        return grade
    if 60 >= marks > 50:
        grade = 'C1'
        return grade
    if 50 >= marks > 40:
        grade = 'C2'
        return grade
    if 40 >= marks > 32:
        grade = 'D'
        return grade
    if marks <= 32:
        grade = 'E'
        return grade


# we need to exempt this view from csrf verification. Will be updated in next version when
# we will implement authentication


@csrf_exempt
def prepare_results(request, school_id, the_class, section):
    prac_subjects = ["Biology", "Physics", "Chemistry", "Fine Arts",
                     "Accountancy", "Business Studies", "Economics",
                     "Information Practices", "Informatics Practices", "Computer Science", "Painting",
                     "Physical Education"]
    school = School.objects.get(id=school_id)
    school_name = school.school_name
    print(school)
    standard = Class.objects.get(school=school, standard=the_class)
    print(standard)
    sec = Section.objects.get(school=school, section=section)
    print(sec)

    # 04/01/2018 get the logos
    try:
        conf = Configurations.objects.get(school=school)
        short_name = conf.school_short_name
    except Exception as e:
        print('failed to retrieve the shore name for %s' % school_name)
        print('exception 04022018-A from exam views.py %s %s' % (e.message, type(e)))

    higher_classes = ['XI', 'XII']
    ninth_tenth = ['IX', 'X']
    middle_classes = ['V', 'VI', 'VII', 'VIII']

    if request.method == 'GET':
        print(request.body)
        whole_class = request.GET.get('whole_class')
        print(whole_class)
        selected_student = request.GET.get('selected_student')
        print (selected_student)

        if whole_class == 'true':
            pdf_name = the_class + '-' + section + '_Term1_Results.pdf'
        else:
            adm_no = selected_student.partition('(')[-1].rpartition(')')[0]
            s = Student.objects.get(school=school, student_erp_id=adm_no)
            print(s)
            pdf_name = s.fist_name + '_' + s.last_name + '_Term1_Results.pdf'
        print(pdf_name)

        response = HttpResponse(content_type='application/pdf')
        content_disposition = 'attachment; filename=' + pdf_name
        print (content_disposition)
        response['Content-Disposition'] = content_disposition
        print(response)

        c = canvas.Canvas(response, pagesize=A4, bottomup=1)

        font = 'Times-Bold'
        c.setFont(font, 14)
        font = 'Times-Bold'
        top = 700
        line_top = top - 10
        session_top = line_top - 15
        report_card_top = session_top - 10
        stu_detail_top = report_card_top - 20
        if the_class not in higher_classes:
            table1_top = stu_detail_top - 265
        else:
            table1_top = stu_detail_top - 200
        if the_class in ninth_tenth:
            table1_top = stu_detail_top - 220
        print('table1_top at the time of declaration = %i' % table1_top)
        tab = 80

        # get logos
        try:
            logo_url = 'https://s3-us-west-2.amazonaws.com/classup2/media/dev/school_logos/%s/%s.png' % \
                       (short_name, short_name)
            print('logo_url = %s' % logo_url)
            resp = requests.get(logo_url)
            school_logo = Image.open(StringIO.StringIO(resp.content))

            cbse_logo_url = 'https://s3-us-west-2.amazonaws.com/classup2/media/dev/cbse_logo/Logo/cbse-logo.png'
            resp = requests.get(cbse_logo_url)
            cbse_logo = Image.open(StringIO.StringIO(resp.content))
        except Exception as e:
            print('failed to insert logo in the marksheet')
            print('exception 04022018-B from exam views.py %s %s' % (e.message, type(e)))

        c.setFont(font, 14)

        if the_class in higher_classes:
            style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                      ('BOX', (0, 0), (-1, -1), 1, colors.black),
                      ('TOPPADDING', (0, 0), (-1, -1), 1),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                      ('ALIGN', (1, 0), (10, 0), 'CENTER'),
                      ('ALIGN', (11, 0), (14, 0), 'CENTER'),
                      ('SPAN', (1, 0), (10, 0)),
                      ('SPAN', (11, 0), (14, 0)),
                      ('SPAN', (3, 1), (5, 1)),
                      ('SPAN', (8, 1), (10, 1)),
                      ('LINEABOVE', (0, 1), (0, 1), 1, colors.white),
                      ('LINEABOVE', (0, 2), (0, 2), 1, colors.white),
                      ('FONTSIZE', (0, 0), (-1, -1), 7),
                      ('FONT', (0, 0), (14, 0), 'Times-Bold'),
                      ('FONT', (0, 1), (14, 1), 'Times-Bold'),
                      ('FONT', (0, 2), (14, 2), 'Times-Bold'),
                      ('FONT', (0, 2), (14, 1), 'Times-Bold')
                      ]
            style2 = style3 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                               ('BOX', (0, 0), (-1, -1), 1, colors.black),
                               ('TOPPADDING', (0, 0), (-1, -1), 1),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                               ('SPAN', (0, 0), (1, 0)),
                               ('FONTSIZE', (0, 0), (-1, -1), 8),
                               ('FONT', (0, 0), (1, 0), 'Times-Bold')]
        if the_class in middle_classes:
            print('result being prepared for %s, a middle class. Hence both Term1 & Term2 results to be shown.' %
                  the_class)
            style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                      ('BOX', (0, 0), (-1, -1), 1, colors.black),
                      ('TOPPADDING', (0, 0), (-1, -1), 1),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                      ('ALIGN', (1, 0), (6, 0), 'CENTER'),
                      ('ALIGN', (7, 0), (12, 0), 'CENTER'),
                      ('SPAN', (1, 0), (6, 0)),
                      ('SPAN', (7, 0), (12, 0)),
                      ('FONTSIZE', (0, 0), (-1, -1), 7),
                      ('FONT', (0, 0), (12, 0), 'Times-Bold'),
                      ('FONT', (0, 1), (0, 1), 'Times-Bold')]

            style2 = style3 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                                ('TOPPADDING', (0, 0), (-1, -1), 1),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('ALIGN', (0, 0), (1, 0), 'RIGHT'),
                                ('ALIGN', (2, 0), (3, 0), 'RIGHT'),
                                ('SPAN', (0, 0), (1, 0)),
                                ('SPAN', (2, 0), (3, 0)),
                                ('FONTSIZE', (0, 0), (-1, -1), 8),
                                ('FONT', (0, 0), (1, 0), 'Times-Bold'),
                                ('FONT', (2, 0), (3, 0), 'Times-Bold')]
        if the_class in ninth_tenth:
            print('result being prepared for class %s, hence only final Term Results will be prepared' % the_class)
            style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('BOX', (0, 0), (-1, -1), 1, colors.black),
                        ('TOPPADDING', (0, 0), (-1, -1), 1),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (1, 0), (6, 0), 'CENTER'),
                        ('SPAN', (1, 0), (6, 0)),
                        ('FONTSIZE', (0, 0), (-1, -1), 7),
                        ('FONT', (0, 0), (6, 0), 'Times-Bold'),
                        ('FONT', (0, 1), (0, 1), 'Times-Bold')]

            style2 = style3 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                                ('TOPPADDING', (0, 0), (-1, -1), 1),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('ALIGN', (0, 0), (1, 0), 'RIGHT'),
                                ('SPAN', (0, 0), (1, 0)),
                                ('FONTSIZE', (0, 0), (-1, -1), 8),
                                ('FONT', (0, 0), (1, 0), 'Times-Bold')]

        style4 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black), ('TOPPADDING', (0, 0), (-1, -1), 1),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 1), ('FONT', (0, 0), (1, 0), 'Times-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 6)]

        data4 = [['MARKS RANGE', 'GRADE'],
                 ['91 - 100', 'A 1'],
                 ['81 - 90', 'A 2'],
                 ['71 - 80', 'B 1'],
                 ['61 - 70', 'B 2'],
                 ['51 - 60', 'C 1'],
                 ['41 - 50', 'C 2'],
                 ['33 - 40', 'D'],
                 ['32 & Below', 'E (Needs improvement)']]
        session = 'Academic Session 2017-18'
        adm_no_lbl = 'Admission No:'
        stu_name_lbl = 'Student Name:'
        father_name_lbl = 'Mother/Father Name:'
        dob_lbl = 'Date of Birth:'
        class_sec_lbl = 'Class/Section:'

        exam = Exam.objects.get(school=school, title='Term1')
        print(exam)

        sub_dict = {}

        left_margin = -30

        def marksheet(c, s):
            c.translate(inch, inch)
            c.drawInlineImage(school_logo, 410, 690, width=50, height=50)
            c.drawInlineImage(cbse_logo, left_margin, 690, width=60, height=50)
            c.drawString(141, top, school_name)
            c.line(-30, line_top, 6.75 * inch, line_top)

            c.setFont(font, 10)
            c.drawString(152, session_top, session)
            print('heading created')

            report_card = 'Report Card for Class ' + the_class + '-' + section
            c.drawString(152, report_card_top, report_card)

            c.setFont(font, 10)
            c.drawString(left_margin, stu_detail_top, adm_no_lbl)
            c.drawString(tab, stu_detail_top, s.student_erp_id)

            c.drawString(left_margin, stu_detail_top - 15, stu_name_lbl)
            c.drawString(tab, stu_detail_top - 15, s.fist_name + ' ' + s.last_name)

            c.drawString(left_margin, stu_detail_top - 30, father_name_lbl)

            # 19/03/2018 We need to show both mother & father's name
            try:
                additional_details = AdditionalDetails.objects.get(student=s)
                mother_name = additional_details.mother_name
            except Exception as e:
                print('exception 19032018-A from exam views.py %s %s' % (e.message, type(e)))
                print('failed to retrieve mother name for %s %s' % (s.fist_name, s.last_name))
                mother_name = ' '
            parent_name = '%s / Mr. %s' % (mother_name, s.parent.parent_name)
            c.drawString(tab, stu_detail_top - 30, parent_name)

            c.drawString(left_margin, stu_detail_top - 45, dob_lbl)
            try:
                d = DOB.objects.get(student=s)
                dob = d.dob
                print(dob)
                c.drawString(tab, stu_detail_top - 45, dob.strftime('%d-%m-%Y'))
            except Exception as e:
                print ('date of birth not yet set for %s %s ' % (s.fist_name, s.last_name))
                print('Exception 23102017-A from exam views.py %s %s ' % (e.message, type(e)))

            c.drawString(left_margin, stu_detail_top - 60, class_sec_lbl)
            c.drawString(tab, stu_detail_top - 60, the_class + '-' + section)
            print('report heading prepared')

            c.setFont(font, 8)
            if the_class in higher_classes:
                print('result being prepared for class %s. This will be in school own format' % the_class)

                data1 = [['', 'TERM RESULT', '', '', '', '', '', '', '', '', '', 'CUMULATIVE RESULT', '', '', ''],
                         ['\nSUBJECT', 'UT-I', 'UT-II', 'Half Yearly\nExam', '', '',
                          'UT-III', 'UT-IV', 'Final Exam', '', '', 'Unit\nTest', 'Half Yearly\nExam',
                          'Final\nExam', 'Total'],
                         ['', '25', '25', 'Th', 'Pr', 'Tot', '25', '25', 'Th', 'Pr', 'Tot', '25', '25', '50', '100']]
                print('class %s is a higher class. Subject list will come from the student/subject mapping' % the_class)
                sequence = 0
                mapping = HigherClassMapping.objects.filter(student=s)
                for m in mapping:
                    sub_dict[sequence] = m.subject.subject_name
                    sequence = sequence + 1
                print('subjects chosen by %s %s are = ' % (s.fist_name, s.last_name))
                print(sub_dict)

                # 24/02/2018 - now need to set the subject in order
                maths_stream = ['English', 'Mathematics', 'Physics', 'Chemistry']
                bio_stream = ['English', 'Biology', 'Physics', 'Chemistry']
                commerce_stream = ['English', 'Economics', 'Accountancy', 'Business Studies']

                try:
                    print('now determining the stream chosen by %s %s...' % (s.fist_name, s.last_name))
                    if 'Mathematics' in sub_dict.values():
                        chosen_stream = maths_stream
                        print('%s %s has chosen %s stream' % (s.fist_name, s.last_name, 'maths'))
                    if 'Biology' in sub_dict.values():
                        chosen_stream = bio_stream
                        print('%s %s has chosen %s stream' % (s.fist_name, s.last_name, 'biology'))
                    if 'Economics' in sub_dict.values():
                        chosen_stream = commerce_stream
                        print('%s %s has chosen %s stream' % (s.fist_name, s.last_name, 'commerce'))
                except Exception as e:
                    print('failed to determine the stream chosen by %s %s' % (s.fist_name, s.last_name))
                    print('exception 24022018-A from exam views.py %s %s' % (e.message, type(e)))

                # now find the elective subject
                elective_sub = (set(sub_dict.values()) ^ set(chosen_stream)).pop()
                print('elective chosen by %s %s: %s' % (s.fist_name, s.last_name, elective_sub))

                # complete the list of all subjects chosen by this student
                chosen_stream.append(elective_sub)
                print('complete list of subjects chosen by %s %s: ' % (s.fist_name, s.last_name))
                print(chosen_stream)

                # 25/02/2018 - currently hard coding the test list. Ideally it should come from database

                exam_list = ['UT I', 'UT II', 'Half Yearly', 'UT III', 'UT IV', 'Final Exam']
                term_exams = ['Half Yearly', 'Final Exam']
                try:
                    for sub in chosen_stream:
                        sub_row = [sub]
                        print('sub_row at this stage = ')
                        print(sub_row)
                        print('now retrieving all test marks for %s %s in %s' % (s.fist_name, s.last_name, sub))
                        subject = Subject.objects.get(school=school, subject_name=sub)
                        ut_total = 0.0
                        for an_exam in exam_list:
                            try:
                                exam = Exam.objects.get(school=school, title=an_exam)
                                try:
                                    test = ClassTest.objects.get(subject=subject, the_class=standard, section=sec,
                                                                 date_conducted__range=(exam.start_date, exam.end_date))
                                    print('test was conducted for %s under exam: %s for class %s' %
                                          (sub, an_exam, the_class))
                                    print(test)
                                    result = TestResults.objects.get(class_test=test, student=s)
                                    marks = float(result.marks_obtained)
                                    if marks < 0.0:
                                        marks = 'ABS'
                                    if exam.title not in term_exams:
                                        if float(test.max_marks) != 25.0:
                                            print('max marks for %s in %s were %f. Conversion is required' %
                                                  (sub, exam.title, float(test.max_marks)))
                                            marks = round((25*marks)/float(test.max_marks), 2)
                                            if marks < 0.0:
                                                marks = 'ABS'
                                        ut_total = ut_total + marks
                                    sub_row.append(marks)
                                    if exam.title in term_exams:
                                        # this is a half yearly or annual exam. The possibility of practical marks...
                                        try:
                                            term_test_results = TermTestResult.objects.get(test_result=result)
                                            if sub in prac_subjects:
                                                print('%s has practical component' % (sub))
                                                prac_marks = float(term_test_results.prac_marks)
                                                if prac_marks < 0.0:
                                                    prac_marks = ' '
                                                    tot_marks = marks
                                                else:
                                                    # 26032018 - there is a possibility that student was absent
                                                    # in theory but present in practical
                                                    if marks >= 0.0:
                                                        tot_marks = marks + prac_marks
                                                    else:
                                                        tot_marks = prac_marks
                                            else:
                                                print('%s does not have practical component' % (sub))
                                                prac_marks = 'NA'
                                                tot_marks = marks
                                            sub_row.append(prac_marks)
                                            sub_row.append(tot_marks)

                                            if exam.title == term_exams[0]:
                                                half_yearly_marks = tot_marks
                                            if exam.title == term_exams[1]:
                                                final_marks = tot_marks
                                        except Exception as e:
                                            print('subject %s has no practical component' % (sub))
                                            print('exception 27022018-A from exam views.py %s %s'
                                                  % (e.message, type(e)))
                                except Exception as e:
                                    print('no test has been created for %s for exam %s for class %s' %
                                          (sub, exam.title, the_class))
                                    print('exception 28022018-A from exam views.py %s %s' % (e.message, type(e)))
                                    marks = 'ABS'
                                    sub_row.append(marks)
                                    # if it was a Half Yearly or Final exam we need to take care of prac & total marks
                                    if exam.title in term_exams:
                                        if sub in prac_subjects:
                                            prac_marks = ' '
                                        else:
                                            prac_marks = 'NA'
                                        sub_row.append(prac_marks)
                                        sub_row.append(' ')
                            except Exception as e:
                                print('failed to retrieve any test for subject %s associated with exam %s for class %s' %
                                            (sub, an_exam, the_class))
                                print('exception 25022018-B from exam views.py %s %s' % (e.message, type(e)))
                        # calculate the cumulative result for this subject. UTs & Half yearly weightage is 25% each
                        #  & final exam weightage is 50%
                        try:
                            ut_cumul = round(ut_total/float(4), 2)
                            sub_row.append(ut_cumul)
                            half_year_cumul = round(half_yearly_marks/float(4), 2)
                            sub_row.append(half_year_cumul)
                            final_cumul = round(final_marks/float(2), 2)
                            sub_row.append(final_cumul)
                            grand_total = ut_cumul + half_year_cumul + final_cumul
                            sub_row.append(grand_total)
                        except Exception as e:
                            print('failed to enter Cumulative Result. This may be because certain marks not entered')
                            print('exception 01032018-A from exam views.py %s %s' % (e.message, type(e)))
                        data1.append(sub_row)
                        print('data1 = ')
                        print(data1)
                    table1 = Table(data1)
                    table1.setStyle(TableStyle(style1))
                    table1.wrapOn(c, left_margin, 0)
                    table1.drawOn(c, left_margin, table1_top)
                    print('table1 drawn for %s %s' % (s.fist_name, s.last_name))
                    theory_prac_split = 'Physics, Chemistry, Comp. Sc., Info. Prac., Biology, Phy. Edu., Eco, AccTB - '
                    theory_prac_split += '  Max Marks: Theory-70, Practical-30'
                    c.drawString(left_margin, table1_top - 20, theory_prac_split)
                    theory_prac_split = 'English, Mathematics - Max Marks: Theory-100, Prac: Not Applicable (NA)'
                    c.drawString(left_margin, table1_top-30, theory_prac_split)
                except Exception as e:
                    print('Error while preparing results for class: %s' % (the_class))
                    print ('Exception 25022018-A from exam views.py %s %s' % (e.message, type(e)))

                # get the CoScholastic Grades for this student
                print('getting the Coscholastic grades for %s %s' % (s.fist_name, s.last_name))
                table2_top = table1_top - 100
                try:
                    data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale]', '']]
                    work_array = []
                    art_array = []
                    health_array = []
                    dscpln_array = []

                    try:
                        co_scl = CoScholastics.objects.get(term='Term2', student=s)
                        work_array.append('General Studies (GS)')
                        work_ed = co_scl.work_education
                        work_array.append(work_ed)

                        art_array.append('Work Experience (Work Exp.)')
                        art_ed = co_scl.art_education
                        art_array.append(art_ed)

                        health_array.append('Health & Physical Education')
                        health_ed = co_scl.health_education
                        health_array.append(health_ed)

                        dscpln_array.append('Discipline: Term-1[On a 3-point(A-C) grading scale]')
                        dscpln = co_scl.discipline
                        dscpln_array.append(dscpln)
                        remark = co_scl.teacher_remarks
                    except Exception as e:
                        print('failed to retrieve %s Co-scholastic grades for %s %s for ' %
                                    ('Term2', s.fist_name, s.last_name))
                        print('exception 20032017-X from exam views.py %s %s' % (e.message, type(e)))
                except Exception as e:
                    print('failed to retrieve Co-scholastic grades for %s %s for ' % (s.fist_name, s.last_name))
                    print('exception 07022018-B from exam views.py %s %s' % (e.message, type(e)))

                try:
                    data2.append(work_array)
                    data2.append(art_array)
                    data2.append(health_array)
                    table2 = Table(data2)
                    table2.setStyle(TableStyle(style2))
                    table2.wrapOn(c, left_margin, 0)
                    table2.drawOn(c, left_margin, table2_top)
                    print('table2 drawn for %s %s' % (s.fist_name, s.last_name))
                except Exception as e:
                    print('failed to draw table2 for %s %s' % (s.fist_name, s.last_name))
                    print('exception 20032018-Y from exam views.py %s %s' % (e.message, type(e)))

                print('preparing table3 for %s %s' % (s.fist_name, s.last_name))
                table3_top = table2_top - 40
                try:
                    data3 = [['Grade', '']]

                    data3.append(dscpln_array)
                    table3 = Table(data3)
                    table3.setStyle(TableStyle(style3))
                    table3.wrapOn(c, 0, 0)
                    table3.drawOn(c, left_margin, table3_top)
                    print('drawn table3 for %s %s' % (s.fist_name, s.last_name))
                except Exception as e:
                    print('failed to draw table3 for %s %s' % (s.fist_name, s.last_name))
                    print('exception 20032018-Z from exam views.py %s %s' % (e.message, type(e)))
            else:
                # 02/11/2017 - get the scheme for this class. The scheme will provide the subjects of this class and
                # the sequence. Subjects in the Marksheet would appear in the order of sequence
                try:
                    if the_class not in higher_classes:
                        print('class %s is not a higher class. Hence subject list will be as per scheme' % the_class)
                        scheme = Scheme.objects.filter(school=school, the_class=standard)
                        sub_count = scheme.count()
                        for sc in scheme:
                            sub_dict[sc.sequence] = sc.subject
                        print('sub_dict = ')
                        print (sub_dict)

                except Exception as e:
                    print('Looks like the scheme for class %s is not yet set' % the_class)
                    print('exception 10022018-A from exam views.py %s %s' % (e.message, type(e)))
                if the_class in middle_classes:
                    data1 = [['Scholastic\nAreas', 'Term-1 (100 Marks)', '', '', '', '', '',
                              'Term-2 (100 Marks)', '', '', '', '', ''],
                             ['Sub Name', 'Per Test\n(10)', 'Note Book\n(5)', 'Sub\nEnrichment\n(5)',
                              'Half\nYearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade',
                              'Per Test\n(10)', 'Note Book\n(5)', 'Sub\nEnrichment\n(5)',
                              'Yearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade']]
                if the_class in ninth_tenth:
                    data1 = [['Scholastic\nAreas', 'Academic Year (100 Marks)', '', '', '', '', ''],
                             ['Sub Name', 'Per Test\n(10)', 'Note Book\n(5)', 'Sub\nEnrichment\n(5)',
                              'Annual\nExamination\n(80)', 'Marks\nObtained\n(100)', 'Grade']]
                for i in range(0, sub_count):
                    sub = sub_dict.values()[i]
                    print ('sub = %s' % sub)
                    if sub.subject_name == 'Third Language':
                        print ('determining third language for %s' % s.fist_name)
                        try:
                            third_lang = ThirdLang.objects.get(student=s)
                            sub = third_lang.third_lang
                            print ('third language for %s is %s' % (s.fist_name, sub.subject_name))
                        except Exception as e:
                            print ('failed to determine third lang for %s. Exception 061117-B from exam views.py %s %s'
                                   % (s.fist_name, e.message, type(e)))
                    sub_row = [sub.subject_name]
                    terms = ['Term1', 'Term2']
                    try:
                        for term in terms:
                            # for class IX, only the result of Term2, ie the final exam is to be shown
                            if term == 'Term1' and the_class in ninth_tenth:
                                continue

                            exam = Exam.objects.get(school=school, title=term)
                            print(exam)
                            start_date = exam.start_date
                            end_date = exam.end_date
                            try:
                                test = ClassTest.objects.get(subject=sub, the_class=standard, section=sec,
                                                             date_conducted__gte=start_date,
                                                             date_conducted__lte=end_date)
                                tr = TestResults.objects.get(class_test=test, student=s)

                                if sub.subject_name == 'GK':
                                    pa = 'NA'
                                    sub_enrich = 'NA'
                                    main = 'NA'
                                    notebook = 'NA'
                                    total = 'NA'
                                    grade = tr.grade
                                else:
                                    ttr = TermTestResult.objects.get(test_result=tr)
                                    pa = ttr.periodic_test_marks
                                    notebook = ttr.note_book_marks
                                    sub_enrich = ttr.sub_enrich_marks
                                    main = tr.marks_obtained
                                    total = float(main) + float(pa) + float(notebook) + float(sub_enrich)
                                    # in case the student was absent we need to show ABS in the marksheet.
                                    if float(main) < 0.0:
                                        main = 'ABS'
                                        total = float(pa) + float(notebook) + float(sub_enrich)
                                    grade = get_grade(total)
                                    print('grade obtained by %s in %s exam of %s: %s' %
                                          (s.fist_name, term, sub.subject_name, grade))
                                if total > -1000.0:
                                    sub_row.append(pa)
                                    sub_row.append(notebook)
                                    sub_row.append(sub_enrich)
                                    sub_row.append(main)
                                    sub_row.append(total)
                                    sub_row.append(grade)

                            except Exception as e:
                                print('%s test for %s is not yet scheduled' % (term, sub))
                                print('exception 12032018-A from exam views.py %s %s' % (e.message, type(e)))
                        data1.append(sub_row)
                        print('sub_row = ')
                        print(sub_row)
                        print('data1 =')
                        print(data1)
                    except Exception as e:
                        print('Error while preparing results for %s in exam %s' % (sub, term))
                        print ('Exception 21102017-A from exam views.py %s %s' % (e.message, type(e)))
                try:
                    table1 = Table(data1)
                    print('table1 object created')
                    table1.setStyle(TableStyle(style1))
                    table1.wrapOn(c, left_margin, 0)
                    table1.drawOn(c, left_margin, table1_top)
                    print('table1_top = %i' % table1_top)
                    print('table1 drawn for %s %s' % (s.fist_name, s.last_name))
                except Exception as e:
                    print('Error while preparing results')
                    print('Exception 21102017-H from exam views.py %s %s' % (e.message, type(e)))

                # get the CoScholastic Grades for this student
                print('getting the Coscholastic grades for %s %s' % (s.fist_name, s.last_name))
                table2_top = table1_top - 70
                try:
                    if the_class in middle_classes:
                        data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale]', '',
                                'Co-Scholastic Areas: Term-2[On a 3-point(A-C) grading scale]', '']]
                    if the_class in ninth_tenth:
                        data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale]', '']]
                    work_array = []
                    art_array = []
                    health_array = []
                    dscpln_array = []
                    for term in terms:
                        # for class IX, only the result of Term2, ie the final exam is to be shown
                        if term == 'Term1' and the_class in ninth_tenth:
                            continue
                        try:
                            co_scl = CoScholastics.objects.get(term=term, student=s)
                            work_array.append('Work Education (or Pre-vocational Education)')
                            work_ed = co_scl.work_education
                            work_array.append(work_ed)

                            art_array.append('Art Education')
                            art_ed = co_scl.art_education
                            art_array.append(art_ed)

                            health_array.append('Health & Physical Education')
                            health_ed = co_scl.health_education
                            health_array.append(health_ed)

                            dscpln_array.append('Discipline: Term-1[On a 3-point(A-C) grading scale]')
                            dscpln = co_scl.discipline
                            dscpln_array.append(dscpln)
                            remark = co_scl.teacher_remarks
                        except Exception as e:
                            print('failed to retrieve %s Co-scholastic grades for %s %s for ' %
                                  (term, s.fist_name, s.last_name))
                            print('exception 07022018-C from exam views.py %s %s' % (e.message, type(e)))
                except Exception as e:
                    print('failed to retrieve Co-scholastic grades for %s %s for ' % (s.fist_name, s.last_name))
                    print('exception 07022018-B from exam views.py %s %s' % (e.message, type(e)))

                try:
                    data2.append(work_array)
                    data2.append(art_array)
                    data2.append(health_array)
                    table2 = Table(data2)
                    print('table2 object created')
                    print('style2 = ')
                    print(style2)
                    table2.setStyle(TableStyle(style2))
                    table2.wrapOn(c, left_margin, 0)
                    table2.drawOn(c, left_margin, table2_top)
                    print('table2 drawn for %s %s' % (s.fist_name, s.last_name))
                except Exception as e:
                    print('failed to draw table2 for %s %s' % (s.fist_name, s.last_name))
                    print('exception 09022018-B from exam views.py %s %s' % (e.message, type(e)))

                print('preparing table3 for %s %s' % (s.fist_name, s.last_name))
                table3_top = table2_top - 40
                try:
                    if the_class in middle_classes:
                        data3 = [['Grade', '', 'Grade', '']]
                    if the_class in ninth_tenth:
                        data3 = [['Grade', '']]

                    data3.append(dscpln_array)
                    table3 = Table(data3)
                    table3.setStyle(TableStyle(style3))
                    table3.wrapOn(c, 0, 0)
                    table3.drawOn(c, left_margin, table3_top)
                    print('drawn table3 for %s %s' % (s.fist_name, s.last_name))
                except Exception as e:
                    print('failed to draw table3 for %s %s' % (s.fist_name, s.last_name))
                    print('exception 07022018-C from exam views.py %s %s' % (e.message, type(e)))

                try:
                    c.drawString(left_margin, table3_top - 15, 'Class Teacher Remarks: ')
                    c.drawString(tab - 20, table3_top - 15, remark)

                    if the_class not in ninth_tenth:
                        c.drawString(left_margin, table3_top - 25, 'Promoted to Class: ')
                        # get the class to which this student is promoted. Only if he has passed the exam
                        try:
                            not_promoted = NPromoted.objects.get(student=s)
                            print('student %s %s has failed in class %s.' % (s.fist_name, s.last_name, the_class))
                            print(not_promoted)
                            promoted_status = 'Not Promoted'
                        except Exception as e:
                            print('student %s %s has passed in class %s.' % (s.fist_name, s.last_name, the_class))
                            print('exception 02032018-A from exam views.py %s %s' % (e.message, type(e)))
                            try:
                                current_class = Class.objects.get(school=school, standard=the_class)
                                next_class_sequence = current_class.sequence + 1
                                next_class = Class.objects.get(school=school, sequence=next_class_sequence)
                                next_class_standard = next_class.standard
                                promoted_status = next_class_standard
                            except Exception as e:
                                print('%s %s of class %s has passed. But failed to determine his next class' %
                                      (s.fist_name, s.last_name, the_class))
                                print('exception 02032018-B from exam views.py %s %s' % (e.message, type(e)))
                        c.drawString(tab - 20, table3_top - 25, promoted_status)

                    c.drawString(left_margin, table3_top - 55, 'Place & Date:')
                    c.drawString(left_margin + 50, table3_top - 55, 'Noida   26/03/2018')
                    c.drawString(175, table3_top - 55, 'Signature of Class Teacher')
                    c.drawString(400, table3_top - 55, 'Signature of Principal')
                except Exception as e:
                    print('exception 08022018-A from exam views.py %s %s' % (e.message, type(e)))

                c.drawString(170, table3_top - 90, "Instructions")
                c.drawString(0, table3_top - 100, "Grading Scale for Scholastic Areas: "
                                                  "Grades are awarded on a 8-point grading scales as follows - ")
                table4 = Table(data4)
                table4.setStyle(TableStyle(style4))
                table4.wrapOn(c, 0, 0)
                table4.drawOn(c, 140, table3_top - 250)

            # 24/02/2018 - we are re-defining certain variables because in case of higher classes they may have been
            # left undefined till this point
            table2_top = table1_top - 70
            if the_class not in higher_classes:
                table3_top = table2_top - 40
            else:
                table3_top = table2_top - 70
            c.line(left_margin, table3_top - 60, 6.75 * inch, table3_top - 60)
            try:
                if the_class in ninth_tenth:
                    c.drawString(left_margin, table3_top - 25, 'Result: ')
                else:
                    c.drawString(left_margin, table3_top - 25, 'Promoted to Class: ')
                    # get the class to which this student is promoted. Only if he has passed the exam
                    try:
                        not_promoted = NPromoted.objects.get(student=s)
                        print('student %s %s has failed in class %s.' % (s.fist_name, s.last_name, the_class))
                        print(not_promoted)
                        promoted_status = 'Not Promoted'
                    except Exception as e:
                        print('student %s %s has passed in class %s.' % (s.fist_name, s.last_name, the_class))
                        print('exception 02032018-C from exam views.py %s %s' % (e.message, type(e)))
                        try:
                            current_class = Class.objects.get(school=school, standard=the_class)
                            next_class_sequence = current_class.sequence + 1
                            next_class = Class.objects.get(school=school, sequence=next_class_sequence)
                            next_class_standard = next_class.standard
                            promoted_status = next_class_standard
                        except Exception as e:
                            print('%s %s of class %s has passed. But failed to determine his next class' %
                                  (s.fist_name, s.last_name, the_class))
                            print('exception 02032018-D from exam views.py %s %s' % (e.message, type(e)))
                    c.drawString(tab - 20, table3_top - 25, promoted_status)

                c.drawString(tab - 20, table3_top - 25, '')
                c.drawString(left_margin, table3_top - 55, 'Place & Date:')
                c.drawString(left_margin + 50, table3_top - 55, 'Noida   26/03/2018')
                c.drawString(175, table3_top - 55, 'Signature of Class Teacher')
                c.drawString(400, table3_top - 55, 'Signature of Principal')
            except Exception as e:
                print('exception 08022018-A from exam views.py %s %s' % (e.message, type(e)))
            return

        if whole_class == 'true':
            # get the list of all the students, then get the marks of each test conducted for this exam
            students = Student.objects.filter(school=school, current_class=standard, current_section=sec)
            for s in students:
                print('Entering loop')
                marksheet(c, s)
                c.showPage()
        else:
            marksheet(c, s)
            c.showPage()
        try:
            c.save()
        except Exception as e:
            print('error in saving the pdf')
            print ('Exception 21102017-P from exam views.py %s %s' % (e.message, type(e)))
        print('about to send the response')
        return response
    return HttpResponse()


class ResultSheet(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Download Result Sheets'

        if request.session['user_type'] == 'school_admin':
            context_dict['user_type'] = 'school_admin'

        school_id = request.session['school_id']
        form = ResultSheetForm(school_id=school_id)
        context_dict['form'] = form
        return render(request, 'classup/result_sheet.html', context_dict)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Download Result Sheets'

        if request.session['user_type'] == 'school_admin':
            context_dict['user_type'] = 'school_admin'
        if "cancel" in request.POST:
            return render(request, 'classup/result_sheet.html', context_dict)
        else:
            school_id = request.session['school_id']
            school = School.objects.get(id=school_id)
            form = ResultSheetForm(request.POST, school_id=school_id)

            higher_classes = ['XI', 'XII']
            ninth_tenth = ['IX', 'X']
            middle_classes = ['V', 'VI', 'VII', 'VIII']

            if form.is_valid():
                the_class = form.cleaned_data['the_class']
                section = form.cleaned_data['section']
                print ('result sheet will be generated for %s-%s' % (the_class.standard, section.section))

                excel_file_name = 'Result_Sheet_' + str(the_class.standard) + '-' + str(section.section) + '.xlsx'

                output = StringIO.StringIO(excel_file_name)
                workbook = xlsxwriter.Workbook(output)
                result_sheet = workbook.add_worksheet("Result Sheet")

                border = workbook.add_format()
                border.set_border()

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
                cell_normal = workbook.add_format({
                    'align': 'left',
                    'valign': 'top',
                    'text_wrap': True
                })
                cell_normal.set_border()
                cell_center = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'text_wrap': True,
                    'bold': True
                })
                cell_center.set_border()
                vertical_text = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'bold': True,
                    'rotation': 90
                })
                vertical_text.set_border()
                perc_format = workbook.add_format({
                    'num_format': '0.00%',
                    'align': 'center',
                    'valign': 'top',
                    'border': 1
                })
                cell_grade = workbook.add_format({
                    'align': 'center',
                    'valign': 'top',
                    'bold': True,
                    'border': 1
                })
                cell_small = workbook.add_format({
                    'align': 'left',
                    'valign': 'top',
                    'font_size': 8,
                    'bold': True,
                    'border': 1
                })

                school_name = school.school_name + ' ' + school.school_address
                title_text = 'CONSOLIDATED RESULT SHEET (2017-2018) FOR CLASS %s-%s' % \
                             (the_class.standard, section.section)
                print (title_text)
                # get the name of the class teacher
                class_teacher = 'N/A'
                try:
                    ct = ClassTeacher.objects.get(school=school, standard=the_class, section=section)
                    class_teacher = ct.class_teacher.first_name + ' ' + ct.class_teacher.last_name
                except Exception as e:
                    print ('exception 19012018-A from exam views.py %s %s' % (e.message, type(e)))
                    print ('class teacher for class %s-%s is not set!' % (the_class.standard, section.section))
                if the_class.standard in middle_classes:
                    result_sheet.merge_range ('A1:AI1', school_name,  title)
                    result_sheet.merge_range('A2:AI2', title_text, title)
                    result_sheet.merge_range('A3:AI3', ('CLASS TEACHER: %s' % class_teacher), header)
                else:
                    result_sheet.merge_range('A1:AE1', 'JAGRAN PUBLIC SCHOOL NOIDA', title)
                    result_sheet.merge_range('A2:AE2', title_text, title)
                    result_sheet.merge_range('A3:AE3', ('CLASS TEACHER: %s' % class_teacher), header)

                # headings that are common for all the classes
                if the_class.standard in higher_classes:
                    print('headings been prepared for higher class %s' % the_class)
                    # for higher classes we need an extra row to show practical & theory marks
                    result_sheet.merge_range('A4:A6', 'S No', cell_center)
                    result_sheet.merge_range('B4:B6', 'Admn. No\nReg. No', cell_center)
                    result_sheet.set_column('A:A', 3)
                    result_sheet.set_column('C:C', 4)
                    result_sheet.merge_range('C4:C6', 'House', vertical_text)
                    result_sheet.set_column('D:D', 18)
                    result_sheet.merge_range('D4:D6', 'Student Name', cell_center)
                else:
                    print('heading been prepared for middle or ninth/tenth class %s' % the_class)
                    result_sheet.merge_range('A4:A7', 'S No', cell_center)
                    result_sheet.merge_range('B4:B7', 'Admn. No\nReg. No', cell_center)
                    result_sheet.set_column('A:A', 3)
                    result_sheet.set_column('C:C', 4)
                    result_sheet.merge_range('C4:C7', 'House', vertical_text)
                    result_sheet.set_column('D:D', 18)
                    result_sheet.merge_range('D4:D7', 'Student Name', cell_center)

                if the_class.standard in middle_classes:
                    result_sheet.merge_range ('E4:O4', 'Term I (700)', cell_center)
                    result_sheet.merge_range ('P4:Z4', 'Term II (700)', cell_center)
                    result_sheet.set_column ('E:AC', 6)
                    result_sheet.set_column ('AD:AI', 3)
                    result_sheet.set_column ('G:G', 6.5)
                    result_sheet.set_column ('R:R', 6.5)

                    result_sheet.merge_range (3, 26, 3, 28, 'Overall', cell_center)
                    result_sheet.merge_range (4, 26, 4, 28, '(A+B)', cell_center)
                    result_sheet.merge_range (5, 26, 5, 28, 'Grand Total(1400))', cell_center)
                    result_sheet.merge_range (3, 29, 6, 29, 'Rank', vertical_text)
                    result_sheet.merge_range (3, 30, 6, 30, 'Work Ed.', vertical_text)
                    result_sheet.merge_range (3, 31, 6, 31, 'Art/Music', vertical_text)
                    result_sheet.merge_range (3, 32, 6, 32, 'Health/Phy Ed.', vertical_text)
                    result_sheet.merge_range (3, 33, 6, 33, 'Discipline', vertical_text)
                    result_sheet.merge_range(3, 34, 6, 34, 'GK', cell_center)
                    result_sheet.merge_range(3, 35, 6, 35, 'Result/Remark', cell_center)
                    result_sheet.set_column ('AJ:AJ', 12)

                    sub_short = ['Eng\n(100)', 'Hindi\n(100)', 'Sanskrit\n(100)', 'French\n(100)', 'Maths\n(100)',
                                 'Science\n(100)', 'SST\n(100)', 'Comp.\n(100)']
                    sub_full = ['English', 'Hindi', 'Sanskrit', 'French', 'Mathematics', 'Science', 'Social Studies',
                                'Computer']
                    col_range = 12
                    for col in range (4, col_range):
                        result_sheet.merge_range (4, col, 6, col, sub_short[col-4], cell_center)
                    result_sheet.merge_range ('M5:O5', '(A)', cell_center)
                    result_sheet.merge_range ('M6:O6', 'Total(700)', cell_center)
                    result_sheet.write_string ('M7', 'Marks', cell_center)
                    result_sheet.write_string ('N7', '%', cell_center)
                    result_sheet.write_string ('O7', 'Grade', cell_center)

                    col_range = 23
                    for col in range(15, col_range):
                        result_sheet.merge_range(4, col, 6, col, sub_short[col - 15], cell_center)
                    result_sheet.merge_range('X5:Z5', '(B)', cell_center)
                    result_sheet.merge_range('X6:Z6', 'Total(700)', cell_center)
                    result_sheet.write_string('X7', 'Marks', cell_center)
                    result_sheet.write_string('Y7', '%', cell_center)
                    result_sheet.write_string('Z7', 'Grade', cell_center)
                    result_sheet.write_string(6, 26, 'Marks', cell_center)
                    result_sheet.write_string(6, 27, '%', cell_center)
                    result_sheet.write_string(6, 28, 'Grade', cell_center)

                    # header rows are ready, now is the time to get the result of each student
                    try:
                        students = Student.objects.filter (school=school, current_class=the_class,
                                                           current_section=section,
                                                           active_status=True).order_by ('fist_name')
                        print ('retrieved the list of students for %s-%s' % (the_class.standard, section.section))
                        print (students)
                        # prepare the borders
                        last_col = 37
                        for row in range(7, students.count() + 7):
                            for col in range(0, last_col):
                                result_sheet.write(row, col, '', border)
                    except Exception as e:
                        print ('exception 20012018-A from exam views.py %s %s' % (e.message, type(e)))
                        print ('failed to retrieve the list of students for %s-%s' %
                               (the_class.standard, section.section))

                    s_no = 1
                    row = 7
                    col = 0
                    for student in students:
                        result_sheet.write_number(row, col, s_no, cell_normal)
                        col = col + 1
                        admission_no = student.student_erp_id
                        result_sheet.write_string(row, col, admission_no, cell_normal)
                        col = col + 1
                        result_sheet.write_string (row, col, '', cell_normal)
                        col = col + 1
                        student_name = student.fist_name + ' ' + student.last_name
                        result_sheet.write_string(row, col, student_name, cell_normal)
                        marks_col = col + 1
                        for s in sub_full:
                            try:
                                subject = Subject.objects.get (school=school, subject_name=s)
                                print ('retrieved the subject object for %s' % s)
                                print (subject)
                            except Exception as e:
                                print ('exception 20012018-B from exam views.py %s %s' % (e.message, type(e)))
                                print ('failed to retrieve subject for %s' % s)
                                continue
                            try:
                                term_tests = ClassTest.objects.filter(the_class=the_class, section=section,
                                                                      subject=subject, test_type='term').\
                                    order_by('date_conducted')
                                print ('retrieved the term tests for class: %s-%s, subject: %s' %
                                       (the_class.standard, section.section, s))
                                print (term_tests)
                                for test in term_tests:
                                    try:
                                        print ('retrieving % s marks for %s' % (s, student_name))
                                        test_result = TestResults.objects.get(class_test=test, student=student)
                                        term_test_result = TermTestResult.objects.get (test_result=test_result)
                                        sub_marks = test_result.marks_obtained + term_test_result.periodic_test_marks
                                        sub_marks = sub_marks + term_test_result.note_book_marks
                                        sub_marks = sub_marks + term_test_result.sub_enrich_marks

                                        # if the subject if third language (Sanskrit/French) and if student has
                                        # not opted for this subject then marks will be -20000.00
                                        if sub_marks < 0:
                                            print ('subject %s is not opted by %s' % (s, student_name))
                                            result_sheet.write_string (row, marks_col, 'NA', cell_grade)
                                            marks_col = marks_col + 11
                                            continue
                                        result_sheet.write_number (row, marks_col, sub_marks, cell_normal)
                                        print ('successfully retrieved %s marks for %s and sheet updated' %
                                               (s, student_name))
                                        # same subject in Term II is 11 columns away ex English in term I is on col E and in
                                        # term II it is on col P
                                        marks_col = marks_col + 11
                                    except Exception as e:
                                        print ('exception 20012018-D from exam views.py %s %s' % (e.message, type(e)))
                                        print ('failed to retrieve %s marks for %s' % (s, student_name))
                            except Exception as e:
                                print ('exception 20012018-C from exam views.py %s %s' % (e.message, type(e)))
                                print ('failed to retrieved the term tests for class: %s-%s, subject: %s' %
                                       (the_class.standard, section.section, s))
                                continue
                            # 22/03/2018 we show GK Grades as well
                            try:
                                gk = Subject.objects.get(school=school, subject_name='GK')
                                gk_tests = ClassTest.objects.filter(the_class=the_class, section=section,
                                                                      subject=gk)
                                tr1 = TestResults.objects.get(class_test=gk_tests.first(), student=student)
                                gk_grade1 = tr1.grade
                                gk_grade = gk_grade1
                                tr2 = TestResults.objects.get(class_test=gk_tests.last(), student=student)
                                gk_grade2 = tr2.grade
                                gk_grade = '%s/%s' % (gk_grade1, gk_grade2)
                                print('GK grade secured by %s: %s' % (student_name, gk_grade))
                            except Exception as e:
                                print('exception 22032018-A from exam views.py %s %s' % (e.message, type(e)))
                                print('could not retrieve the GK grade for %s' % student_name)
                                gk_grade = ' '
                            col = col + 1
                            marks_col = col + 1
                        # now is the time to insert formulas in the designated cells
                        # formulaes for term I
                        cell_range = xl_range(row, 4, row, 11)
                        formula = '=SUM(%s)' % cell_range
                        result_sheet.write_formula(row, 12, formula, cell_normal)
                        cell_range = xl_range(row, 12, row, 12)
                        formula = '=%s/700.00' % cell_range
                        result_sheet.write_formula (row, 13, formula, perc_format)
                        index = 'N%s*100' % str(row+1)
                        print ('index = %s' % index)
                        formula = '=IF(%s > 90, "A1", IF(%s > 80, "A2", IF(%s > 70, "B1", IF(%s > 60, "B2", ' \
                                  'IF(%s > 50, "C1", IF(%s > 40, "C2", IF(%s > 32, "D", "E")))))))' % \
                                  (index, index, index, index, index, index, index)
                        print ('formula for grade = %s' % formula)
                        result_sheet.write_formula (row, 14, formula, cell_grade)

                        # formula for term II
                        cell_range = xl_range(row, 15, row, 22)
                        formula = '=SUM(%s)' % cell_range
                        result_sheet.write_formula(row, 23, formula, cell_normal)
                        formula = '=SUM(%s)/700.00' % cell_range
                        result_sheet.write_formula(row, 24, formula, perc_format)
                        index = 'Y%s*100' % str(row + 1)
                        print ('index = %s' % index)
                        formula = '=IF(%s > 90, "A1", IF(%s > 80, "A2", IF(%s > 70, "B1", IF(%s > 60, "B2", ' \
                                  'IF(%s > 50, "C1", IF(%s > 40, "C2", IF(%s > 32, "D", "E")))))))' % \
                                  (index, index, index, index, index, index, index)
                        print ('formula for grade = %s' % formula)
                        result_sheet.write_formula(row, 25, formula, cell_grade)

                        # formula for overall
                        formula = '=sum(M%s, X%s)' % (str(row+1), str(row+1))
                        result_sheet.write_formula (row, 26, formula, cell_normal)
                        formula = '=AA%s/1400.00' % str(row+1)
                        result_sheet.write_formula (row, 27, formula, perc_format)
                        index = 'AB%s*100' % str(row + 1)
                        print ('index = %s' % index)
                        formula = '=IF(%s > 90, "A1", IF(%s > 80, "A2", IF(%s > 70, "B1", IF(%s > 60, "B2", ' \
                                  'IF(%s > 50, "C1", IF(%s > 40, "C2", IF(%s > 32, "D", "E")))))))' % \
                                  (index, index, index, index, index, index, index)
                        print ('formula for grade = %s' % formula)
                        result_sheet.write_formula(row, 28, formula, cell_grade)

                        # show the result/remarks. In the beginning it will show Promoted,
                        #  but after the analysis is done, it will show the actual result
                        try:
                            not_promoted = NPromoted.objects.get(student=student)
                            print('student %s %s has failed in class %s.' % (student.fist_name,
                                                                             student.last_name, the_class))
                            print(not_promoted)
                            promoted_status = 'Not Promoted'
                        except Exception as e:
                            print('student %s %s has passed in class %s.' % (student.fist_name, student.last_name,
                                                                             the_class))
                            print('exception 25032018-A from exam views.py %s %s' % (e.message, type(e)))
                            promoted_status = 'Promoted'
                        result_sheet.write_string(row, 35, promoted_status, cell_grade)

                        # co-scholastic grades. We will show grades for both terms separated by /, eg B/A
                        try:
                            cs_term1 = CoScholastics.objects.get (term='term1', student=student)
                            work_ed1 = cs_term1.work_education
                            result_sheet.write_string (row, 30, work_ed1, cell_grade)
                            art_ed1 = cs_term1.art_education
                            result_sheet.write_string (row, 31, art_ed1, cell_grade)
                            health_ed1 = cs_term1.health_education
                            result_sheet.write_string (row, 32, health_ed1, cell_grade)
                            discipline1 = cs_term1.discipline
                            result_sheet.write_string (row, 33, discipline1, cell_grade)

                            cs_term2 = CoScholastics.objects.get (term='term2', student=student)
                            work_ed2 = cs_term2.work_education
                            result_sheet.write_string(row, 30, work_ed1 + '/' + work_ed2, cell_grade)
                            art_ed2 = cs_term2.art_education
                            result_sheet.write_string(row, 31, art_ed1 + '/' + art_ed2, cell_grade)
                            health_ed2 = cs_term2.health_education
                            result_sheet.write_string(row, 32, health_ed1 + '/' + health_ed2, cell_grade)
                            discipline2 = cs_term2.discipline
                            result_sheet.write_string(row, 33, discipline1 + '/' + discipline2, cell_grade)
                            result_sheet.write_string(row, 34, gk_grade, cell_grade)
                        except Exception as e:
                            print ('exception 21012018-A from exam views.py %s %s' % (e.message, type(e)))
                            print ('failed to retrieve Co-scholastics grade for %s' % student_name)
                        col = 0
                        row = row + 1
                        s_no = s_no + 1
                if the_class.standard in ninth_tenth:
                    row = 3
                    col = 4
                    result_sheet.merge_range(row, col, row+3, col, 'Sec Lang. opted', vertical_text)
                    col = col + 1
                    result_sheet.set_column('E:E', 6.25)
                    result_sheet.set_column('F:Z', 5.5)
                    result_sheet.merge_range(row, col, row+2, col+2, 'English\n(100)', cell_center)
                    col = col + 3
                    result_sheet.merge_range(row, col, row+2, col+2, 'Hindi/French/Sanskrit\n(100)', cell_center)
                    col = col + 3
                    result_sheet.merge_range(row, col, row+2, col+2, 'Mathematics\n(100', cell_center)
                    col = col + 3
                    result_sheet.merge_range(row, col, row+2, col+2, 'Science\n(100)', cell_center)
                    col = col + 3
                    result_sheet.merge_range(row, col, row+2, col+2, 'Social Studies\n(100)', cell_center)
                    col = col + 3
                    result_sheet.merge_range(row, col, row+2, col+2, 'FIT\n(100)', cell_center)
                    col = col + 3
                    result_sheet.merge_range(row, col, row+2, col+2, 'Grand Total\n(600)', cell_center)

                    row = 6
                    col_range = 23
                    for col in range(5, col_range):
                        if col%3 == 2:
                            result_sheet.write_string(row, col, 'P.N.A\n(20)', cell_center)
                        if col%3 == 0:
                            result_sheet.write_string(row, col, 'Annual\n(80)', cell_center)
                        if col%3 == 1:
                            result_sheet.write_string(row, col, 'Total\n(100)', cell_center)
                    result_sheet.set_column('AA:AE', 3)
                    col = col_range
                    result_sheet.write_string(row, col, 'Marks', cell_center)
                    col = col + 1
                    result_sheet.write_string(row, col, '%', cell_center)
                    col = col + 1
                    result_sheet.write_string(row, col, 'Grade', cell_center)
                    row = row - 3
                    col = col + 1
                    result_sheet.merge_range(row, col, row+3, col, 'Rank', vertical_text)
                    col = col + 1
                    result_sheet.merge_range(row, col, row+3, col, 'Work Ed.', vertical_text)
                    col = col + 1
                    result_sheet.merge_range(row, col, row+3, col, 'Art/Music', vertical_text)
                    col = col + 1
                    result_sheet.merge_range(row, col, row+3, col, 'Health/Phy Ed.', vertical_text)
                    col = col + 1
                    result_sheet.merge_range(row, col, row + 3, col, 'Discipline', vertical_text)
                    col = col + 1
                    result_sheet.set_column('AF:AF', 12)
                    result_sheet.merge_range(row, col, row+3, col, 'Result/Remark', cell_center)
                    row = row + 1

                    sub_list = ['English', 'Third Language', 'Mathematics', 'Science', 'Social Studies', 'Computer']
                    # header rows are ready, now is the time to get the result of each student
                    try:
                        students = Student.objects.filter(school=school, current_class=the_class,
                                                          current_section=section,
                                                          active_status=True).order_by('fist_name')
                        print ('retrieved the list of students for %s-%s' % (the_class.standard, section.section))
                        print (students)
                        # prepare the borders
                        last_col = 32
                        for row in range(7, students.count() + 7):
                            for col in range(0, last_col):
                                result_sheet.write(row, col, '', border)
                    except Exception as e:
                        print ('exception 26012018-A from exam views.py %s %s' % (e.message, type(e)))
                        print ('failed to retrieve the list of students for %s-%s' % (
                        the_class.standard, section.section))

                    row = 7
                    col = 0
                    s_no = 1
                    for student in students:
                        result_sheet.write_number(row, col, s_no, cell_normal)
                        col = col + 1
                        admission_no = student.student_erp_id
                        result_sheet.write_string(row, col, admission_no, cell_normal)
                        col = col + 1
                        result_sheet.write_string(row, col, '', cell_normal)
                        col = col + 1
                        student_name = student.fist_name + ' ' + student.last_name
                        result_sheet.write_string(row, col, student_name, cell_normal)

                        # next column is for mentioning the second language, and marks will start after that. Hence,
                        # incrementing by 2
                        marks_col = col + 2

                        # get the marks of each subject
                        grand_totl = 0
                        for s in sub_list:
                            # if the subject is language, we need to determine which language this student has opted for
                            if s == 'Third Language':
                                try:
                                    mapping = ThirdLang.objects.get(student=student)
                                    subject = mapping.third_lang
                                    # mention this subject name in column 'Second Lang opted'
                                    second_lang = subject.subject_name
                                    print('second language opted by %s: %s' % (student_name, second_lang))
                                    result_sheet.write_string(row, 4, second_lang, cell_normal)
                                except Exception as e:
                                    print('exception 26012018-B from exam views.py %s %s' % (e.message, type(e)))
                                    print('failed to determine the second language opted by %s' % student_name)
                                    marks_col = marks_col + 2
                                    continue
                            else:
                                subject = Subject.objects.get(school=school, subject_name=s)

                            # retrieve the term test for this subject. As this is IX/X class there will
                            # be only one term test
                            print('now retriving marks secured by %s in %s' % (student_name, subject.subject_name))
                            try:
                                term_test = ClassTest.objects.filter(the_class=the_class, section=section,
                                                                  subject=subject, test_type='term').last()
                                print('retrieved term test for %s' % subject.subject_name)
                                print(term_test)
                                # get the test results for this term test
                                test_result = TestResults.objects.get(class_test=term_test, student=student)
                                annual_marks = test_result.marks_obtained
                                term_test_result = TermTestResult.objects.get(test_result=test_result)
                                pna_marks = term_test_result.periodic_test_marks
                                pna_marks = pna_marks + term_test_result.note_book_marks
                                pna_marks = pna_marks + term_test_result.sub_enrich_marks
                                result_sheet.write_number(row, marks_col, pna_marks, cell_normal)
                                marks_col = marks_col + 1
                                result_sheet.write_number(row, marks_col, annual_marks, cell_normal)
                                marks_col = marks_col + 1
                                total_marks = pna_marks + annual_marks
                                result_sheet.write_number(row, marks_col, total_marks, cell_normal)
                                grand_totl = grand_totl + annual_marks
                                marks_col = marks_col + 1
                            except Exception as e:
                                print('exception 27012018-C from exam views.py %s %s' % (e.message, type(e)))
                                print('failed to retrieve term test marks for %s in subject %s' %
                                      (student_name, subject.subject_name))
                                marks_col = marks_col + 3
                        result_sheet.write_number(row, marks_col, grand_totl, cell_normal)
                        marks_col += 1
                        formula = '=X%s/600.00' % str(row + 1)
                        result_sheet.write_formula (row, marks_col, formula, perc_format)
                        marks_col = marks_col + 1
                        index = 'Y%s*100' % str(row + 1)
                        print ('index = %s' % index)
                        formula = '=IF(%s > 90, "A1", IF(%s > 80, "A2", IF(%s > 70, "B1", IF(%s > 60, "B2", ' \
                                  'IF(%s > 50, "C1", IF(%s > 40, "C2", IF(%s > 32, "D", "E")))))))' % \
                                  (index, index, index, index, index, index, index)
                        print ('formula for grade = %s' % formula)
                        result_sheet.write_formula(row, marks_col, formula, cell_grade)
                        marks_col = marks_col + 2

                        # co-scholastic grades. We will show grades for both terms separated by /, eg B/A.
                        # As this is IX class there will be term2
                        result_sheet.set_column('AE:AI', 10)
                        try:
                            cs_term2 = CoScholastics.objects.get(term='term2', student=student)
                            work_ed = cs_term2.work_education
                            result_sheet.write_string(row, marks_col, work_ed, cell_grade)
                            marks_col = marks_col + 1
                            art_ed = cs_term2.art_education
                            result_sheet.write_string(row, marks_col, art_ed, cell_grade)
                            marks_col = marks_col + 1
                            health_ed = cs_term2.health_education
                            result_sheet.write_string(row, marks_col, health_ed, cell_grade)
                            marks_col = marks_col + 1
                            discipline = cs_term2.discipline
                            result_sheet.write_string(row, marks_col, discipline, cell_grade)
                        except Exception as e:
                            print('exception 27012018-D from exam views.py %s %s' % (e.message, type(e)))
                            print('failed to retrieve Co-scholastic grades for %s' % student_name)
                        marks_col += 1

                        # show the result/remarks. In the beginning it will show Promoted,
                        #  but after the analysis is done, it will show the actual result
                        try:
                            not_promoted = NPromoted.objects.get(student=student)
                            print('student %s %s has failed in class %s.' % (student.fist_name,
                                                                             student.last_name, the_class))
                            print(not_promoted)
                            promoted_status = 'Not Promoted'
                        except Exception as e:
                            print('student %s %s has passed in class %s.' % (student.fist_name, student.last_name,
                                                                             the_class))
                            print('exception 25032018-B from exam views.py %s %s' % (e.message, type(e)))
                            promoted_status = 'Promoted'
                        result_sheet.write_string(row, marks_col, promoted_status, cell_grade)

                        col = 0
                        s_no = s_no + 1
                        row = row + 1
                if the_class.standard in higher_classes:
                    maths_stream = ['English', 'Mathematics', 'Physics', 'Chemistry', 'Elective']
                    bio_stream = ['English', 'Biology', 'Physics', 'Chemistry', 'Elective']
                    commerce_stream = ['English', 'Economics', 'Accountancy', 'Business Studies', 'Elective']
                    components = ['UT', 'Half Yearly', 'Final Exam', 'Cumulative']
                    try:
                        students = Student.objects.filter(school=school, current_class=the_class,
                                                          current_section=section,
                                                          active_status=True).order_by('fist_name')
                        print ('retrieved the list of students for %s-%s' % (the_class.standard, section.section))
                        print (students)
                        last_col = 68
                        for row in range(6, students.count() + 7):
                            for col in range(0, last_col):
                                result_sheet.write(row, col, '', border)
                        for student in students:
                            sub_dict = []
                            # for higher classes we need to determine the stream selected by
                            # student as well as the elective
                            mapping = HigherClassMapping.objects.filter(student=student)
                            for m in mapping:
                                sub_dict.append(m.subject.subject_name)
                            print('subjects chosen by %s %s are = ' % (student.fist_name, student.last_name))
                            print(sub_dict)
                            try:
                                print('now determining the stream for this class %s-%s...' %
                                      (the_class.standard, section.section))
                                if 'Mathematics' in sub_dict:
                                    chosen_stream = maths_stream
                                    print('%s-%s has chosen %s stream' %
                                          (the_class.standard, section.section, 'maths'))
                                if 'Biology' in sub_dict:
                                    chosen_stream = bio_stream
                                    print('%s %s has chosen %s stream' %
                                          (the_class.standard, section.section, 'biology'))
                                if 'Economics' in sub_dict:
                                    chosen_stream = commerce_stream
                                    print('%s %s has chosen %s stream' %
                                          (the_class.standard, section.section, 'commerce'))
                            except Exception as e:
                                print('failed to determine the stream chosen by %s %s' %
                                      (student.fist_name, student.last_name))
                                print('exception 03032018-A from exam views.py %s %s' % (e.message, type(e)))
                            row = 3
                            col = 4
                            result_sheet.merge_range(row, col, row + 2, col, 'Elective Sub', vertical_text)
                            col = col + 1
                            result_sheet.set_column('E:E', 10)
                            result_sheet.set_column('F:BH', 4.5)
                            for sub in chosen_stream:
                                print('now creating heading for subject: %s' % sub)
                                result_sheet.merge_range(row, col, row, col + 10, sub, cell_center)
                                col1 = col

                                # UT
                                result_sheet.merge_range(row+1, col1, row+2, col1, components[0], cell_center)
                                col1 = col1 + 1

                                # Half Yearly Exam
                                result_sheet.merge_range(row+1, col1, row+1, col1+2, components[1], cell_center)
                                result_sheet.write_string(row+2, col1, 'Th', cell_center)
                                col1 += 1
                                result_sheet.write_string(row + 2, col1, 'Pr', cell_center)
                                col1 += 1
                                result_sheet.write_string(row + 2, col1, 'Total', cell_center)
                                result_sheet.set_column(col1, col1, options={'hidden': True})
                                col1 += 1

                                # Final Exam
                                result_sheet.merge_range(row + 1, col1, row + 1, col1 + 2, components[2], cell_center)
                                result_sheet.write_string(row + 2, col1, 'Th', cell_center)
                                col1 += 1
                                result_sheet.write_string(row + 2, col1, 'Pr', cell_center)
                                col1 += 1
                                result_sheet.write_string(row + 2, col1, 'Total', cell_center)
                                result_sheet.set_column(col1, col1, options={'hidden': True})
                                col1 += 1

                                # Cumulative
                                result_sheet.merge_range(row + 1, col1, row + 1, col1 + 3, components[3], cell_center)
                                result_sheet.write_string(row + 2, col1, 'UT\n(25%)', cell_center)
                                col1 += 1
                                result_sheet.write_string(row + 2, col1, 'HY\n(25%)', cell_center)
                                col1 += 1
                                result_sheet.write_string(row + 2, col1, 'Final\n(50%)', cell_center)
                                col1 += 1
                                result_sheet.write_string(row + 2, col1, 'Total', cell_center)

                                col = col + 11
                            break
                        g_col = 60
                        result_sheet.merge_range(row, g_col, row+2, g_col, 'Grand Total', vertical_text)
                        g_col += 1
                        result_sheet.merge_range(row, g_col, row + 2, g_col, 'Percentage', vertical_text)
                        g_col += 1
                        result_sheet.merge_range(row, g_col, row + 2, g_col, 'Grade', vertical_text)
                        g_col += 1
                        result_sheet.merge_range(row, g_col, row + 2, g_col, 'GS', vertical_text)
                        g_col += 1
                        result_sheet.merge_range(row, g_col, row + 2, g_col, 'Work Ex', vertical_text)
                        g_col += 1
                        result_sheet.merge_range(row, g_col, row + 2, g_col, 'PHED', vertical_text)
                        g_col += 1
                        result_sheet.merge_range(row, g_col, row + 2, g_col, 'Discipline', vertical_text)
                        g_col += 1
                        result_sheet.merge_range(row, g_col, row + 2, g_col, 'Result', vertical_text)
                        row += 3

                        # delete the "Elective" entry from the sub_dict. We will now substitute it with the real
                        # elective chosen by each student.
                        chosen_stream.pop()

                        ut_list = ['UT I', 'UT II', 'UT III', 'UT IV']
                        term_exams = ['Half Yearly', 'Final Exam']
                        prac_subjects = ["Biology", "Physics", "Chemistry", "Fine Arts",
                                         "Accountancy", "Business Studies", "Economics",
                                         "Information Practices", "Informatics Practices", "Computer Science",
                                         "Painting",
                                         "Physical Education"]
                        s_no = 1
                        for student in students:
                            col = 0
                            result_sheet.write_number(row, col, s_no, cell_normal)
                            col += 1
                            admission_no = student.student_erp_id
                            result_sheet.write_string(row, col, admission_no, cell_normal)
                            col += 1
                            result_sheet.write_string(row, col, '', cell_normal)
                            col += 1
                            student_name = student.fist_name + ' ' + student.last_name
                            result_sheet.write_string(row, col, student_name, cell_normal)
                            col += 1

                            sub_dict = []
                            mapping = HigherClassMapping.objects.filter(student=student)
                            for m in mapping:
                                sub_dict.append(m.subject.subject_name)
                            print('subjects chosen by %s %s are = ' % (student.fist_name, student.last_name))
                            print(sub_dict)
                            # now find the elective subject
                            elective_sub = (set(sub_dict) ^ set(chosen_stream)).pop()
                            result_sheet.write_string(row, col, elective_sub, cell_small)
                            print('elective chosen by %s %s: %s' %
                                  (student.fist_name, student.last_name, elective_sub))
                            col += 1

                            # complete the list of all subjects chosen by this student
                            chosen_stream.append(elective_sub)
                            print('complete list of subjects chosen by %s %s: ' %
                                  (student.fist_name, student.last_name))
                            print(chosen_stream)

                            # start retrieving the marks secured by this student in all tests & exams
                            student_name = student.fist_name + ' ' + student.last_name
                            print('starting to retrieve the marks for %s of class %s-%s' %
                                  (student_name, the_class.standard, section.section))
                            for sub in chosen_stream:
                                print('retrieving UT marks for %s for %s' % (student_name, sub))
                                try:
                                    subject = Subject.objects.get(school=school, subject_name=sub)
                                    print('successfully retrieved the subject object for subject: %s' % sub)
                                    print(subject)
                                except Exception as e:
                                    print('failed to retrieve the subject object for subject: %s' % sub)
                                    print('exception 04032018-A from exams views.py %s %s' % (e.message, type(e)))

                                ut_total = 0.0
                                comments = 'UT details for %s in %s: \n' % (student_name, sub)
                                for ut in ut_list:
                                    comments += '\n%s: ' % ut
                                    try:
                                        print('now trying to retrieve test in %s for subject %s class %s' %
                                              (ut, sub, the_class.standard))
                                        a_ut = Exam.objects.get(school=school, title=ut)
                                        print('retrieved %s for class %s' % (ut, the_class.standard))
                                        print(a_ut)
                                        try:
                                            test = ClassTest.objects.get(subject=subject, the_class=the_class,
                                                                         section=section, date_conducted__range=
                                                                         (a_ut.start_date, a_ut.end_date))
                                            print('test was conducted for %s under exam: %s for class %s' %
                                                  (sub, ut, the_class.standard))
                                            print(test)
                                            result = TestResults.objects.get(class_test=test, student=student)
                                            print(result)
                                            # convert the marks to be out of 25
                                            if float(result.marks_obtained > -1000.0):
                                                comments += '%s/%s' % (str(result.marks_obtained),
                                                                         str(round(test.max_marks, 0)))
                                                print(comments)
                                                marks = (25.0*float(result.marks_obtained))/(float(test.max_marks))
                                                ut_total += marks
                                        except Exception as e:
                                            print('no test could be found corresponding to %s class %s subject %s' %
                                                  (ut, the_class.standard, sub))
                                            print('exception 04032018-B from exam views.py %s %s'
                                                  % (e.message, type(e)))
                                    except Exception as e:
                                        print('%s could not be retrieved for class %s' % (ut, the_class.standard))
                                        print('exception 04032018-C from exam views.py %s %s' % (e.message, type(e)))
                                        col += 1
                                result_sheet.write_number(row, col, round(ut_total/4.0, 2), cell_normal)
                                result_sheet.write_comment(row, col, comments, {'height': 150})
                                col += 1

                                # get the half yearly marks & final exam marks
                                for term in term_exams:
                                    try:
                                        term_exam = Exam.objects.get(school=school, title=term)
                                        test = ClassTest.objects.get(subject=subject, the_class=the_class,
                                                                     section=section, date_conducted__range=
                                                                     (term_exam.start_date, term_exam.end_date))
                                        print('test was conducted for %s under exam: %s for class %s' %
                                              (sub, term, the_class.standard))
                                        print(test)
                                        result = TestResults.objects.get(class_test=test, student=student)
                                        print(result)
                                        result_sheet.write_number(row, col, float(result.marks_obtained), cell_normal)
                                        col += 1

                                        if sub in prac_subjects:
                                            try:
                                                term_test_results = TermTestResult.objects.get(test_result=result)
                                                print('%s has practical component' % (sub))
                                                prac_marks = float(term_test_results.prac_marks)
                                                if prac_marks > -1000.00:
                                                    result_sheet.write_number(row, col, prac_marks, cell_normal)
                                                col += 1
                                            except Exception as e:
                                                print('%s practical marks for %s could not be retrieved' %
                                                      (sub, student_name))
                                                print('exception 04032018-D from exam views.py %s %s' %
                                                      (e.message, type(e)))
                                                col += 1
                                        else:
                                            result_sheet.write_string(row, col, 'NA', cell_normal)
                                            col += 1
                                        cell_range = xl_range(row, col-2, row, col-1)
                                        formula = '=SUM(%s)' % cell_range
                                        result_sheet.write_formula(row, col, formula, cell_normal)
                                        col += 1
                                    except Exception as e:
                                        print('no test could be found corresponding to %s class %s subject %s' %
                                              (ut, the_class.standard, sub))
                                        print('exception 04032018-B from exam views.py %s %s'
                                              % (e.message, type(e)))
                                        col +=3
                                # fill in cumulative results
                                # get the UT cell
                                cell = xl_rowcol_to_cell(row, col-7)
                                formula = '=%s' % cell
                                result_sheet.write_formula(row, col, formula, cell_normal)
                                col += 1

                                # get the half yearly total cell
                                cell = xl_rowcol_to_cell(row, col-5)
                                formula = '=%s/4.0' % cell
                                result_sheet.write_formula(row, col, formula, cell_normal)
                                col += 1

                                # get the final exam total cell
                                cell = xl_rowcol_to_cell(row, col - 3)
                                formula = '=%s/2.0' % cell
                                result_sheet.write_formula(row, col, formula, cell_normal)
                                col += 1

                                # write the grand total
                                cell_range = xl_range(row, col - 3, row, col - 1)
                                formula = '=SUM(%s)' % cell_range
                                result_sheet.write_formula(row, col, formula, cell_normal)
                                col += 1

                            # write the total for all subjects for this student
                            c1 = xl_rowcol_to_cell(row, 15)
                            c2 = xl_rowcol_to_cell(row, 26)
                            c3 = xl_rowcol_to_cell(row, 37)
                            c4 = xl_rowcol_to_cell(row, 48)
                            c5 = xl_rowcol_to_cell(row, 59)
                            formula = '=ROUND(SUM(%s, %s, %s, %s, %s), 1)' % (c1, c2, c3, c4, c5)
                            print('formula for grand total = %s' % formula)
                            result_sheet.write_formula(row, col, formula, cell_normal)
                            col += 1

                            # percentage
                            cell_range = xl_range(row, col-1, row, col-1)
                            formula = '=%s/500.00' % cell_range
                            result_sheet.write_formula(row, col, formula, perc_format)
                            col += 1

                            index = 'BJ%s*100' % str(row)
                            print ('index = %s' % index)
                            formula = '=IF(%s > 90, "A1", IF(%s > 80, "A2", IF(%s > 70, "B1", IF(%s > 60, "B2", ' \
                                        'IF(%s > 50, "C1", IF(%s > 40, "C2", IF(%s > 32, "D", "E")))))))' % \
                                        (index, index, index, index, index, index, index)
                            print ('formula for grade = %s' % formula)
                            result_sheet.write_formula(row, col, formula, cell_grade)
                            col += 1

                            cs_term1 = CoScholastics.objects.get(term='term2', student=student)
                            work_ed1 = cs_term1.work_education
                            result_sheet.write_string(row, col, work_ed1, cell_grade)
                            col += 1
                            art_ed1 = cs_term1.art_education
                            result_sheet.write_string(row, col, art_ed1, cell_grade)
                            col += 1
                            health_ed1 = cs_term1.health_education
                            result_sheet.write_string(row, col, health_ed1, cell_grade)
                            col += 1
                            discipline1 = cs_term1.discipline
                            result_sheet.write_string(row, col, discipline1, cell_grade)
                            col += 1

                            # show the result/remarks. In the beginning it will show Promoted,
                            #  but after the analysis is done, it will show the actual result
                            result_sheet.set_column('BP:BP', 20)
                            try:
                                not_promoted = NPromoted.objects.get(student=student)
                                print('student %s %s has failed in class %s.' % (student.fist_name,
                                                                                 student.last_name, the_class))
                                print(not_promoted)
                                promoted_status = 'Not Promoted'
                            except Exception as e:
                                print('student %s %s has passed in class %s.' % (student.fist_name, student.last_name,
                                                                                 the_class))
                                print('exception 25032018-C from exam views.py %s %s' % (e.message, type(e)))
                                promoted_status = 'Promoted'
                            result_sheet.write_string(row, col, promoted_status, cell_grade)

                            # reset the chosen_stream to standard subjects
                            chosen_stream.pop()
                            row += 1
                            s_no += 1

                    except Exception as e:
                        print('failed to retrieve the list of students for class %s-%s' %
                              (the_class.standard, section.section))
                        print('exception 03032018-B from exam views.py %s %s' % (e.message, type(e)))
                workbook.close()
                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
                response.write(output.getvalue())
                return response
            else:
                error = 'You have missed to select either Class, or Section'
                form = ResultSheetForm(request)
                context_dict['form'] = form
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/result_sheet.html', context_dict)