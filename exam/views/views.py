import ast
import json

from PIL import Image
from decimal import Decimal

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser

from google.cloud import storage

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
from formats.formats import Formats as format

from student.models import Student, DOB, AdditionalDetails, House
from academics.models import Class, Section, Subject, ThirdLang, ClassTest, \
    Exam, TermTestResult, TestResults, CoScholastics, ClassTeacher
from attendance.models import IndividualAttendance

from exam.models import Scheme, HigherClassMapping, NPromoted, Marksheet, Stream, StreamMapping, Wing
from exam.forms import TermResultForm, ResultSheetForm


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


@parser_classes((MultiPartParser,))
class UploadMarks(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, format=None):
        print('resuest = ')
        print(request.FILES)
        context_dict = {

        }

        try:
            print ('now starting to process the uploaded file for marks upload...')
            fileToProcess_handle = request.FILES['computer_marks.xlsx']

            # check that the file uploaded should be a valid excel
            # file with .xls or .xlsx

            # if this is a valid excel file - start processing it
            fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
            sheet = fileToProcess.sheet_by_index(0)
            if sheet:
                print ('Successfully got hold of sheet!')
            for row in range(sheet.nrows):
                # first two rows are header rows
                if row == 0:
                    continue
                else:
                    erp_id = str(sheet.cell(row, 0).value)
                    school = School.objects.get(id=23)
                    try:
                        student = Student.objects.get(school=school, student_erp_id=erp_id)
                        print('now dealing with %s' % student)
                        theory = sheet.cell(row, 5).value
                        practical = sheet.cell(row, 6).value
                        subject = Subject.objects.get(school=school, subject_name='Computer')
                        exam = Exam.objects.get(school=school, title='Term-I (IX - X)')
                        class_test = ClassTest.objects.get(subject=subject, exam=exam,
                                                           the_class=student.current_class,
                                                           section=student.current_section)
                        test_result = TestResults.objects.get(student=student, class_test=class_test)
                        test_result.marks_obtained = float(theory)
                        test_result.save()
                        ttr = TermTestResult.objects.get(test_result=test_result)
                        ttr.prac_marks = float(practical)
                        ttr.save()
                    except Exception as e:
                        print('exception 02102019-A from exam views.py %s %s' % (e.message, type(e)))
        except Exception as e:
            print('exception 02102019-B from exam views.py %s %s' % (e.message, type(e)))
        return render(request, 'classup/setup_index.html', context_dict)


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

                    for col in range(1, 11):
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
                            print('exception 201117-C from exam views.py %s %s' % (e.message, type(e)))
                            try:
                                scheme = Scheme(school=school, the_class=the_class, sequence=sequence, subject=subject)
                                scheme.save()
                                print ('successfully created the scheme of subject %s of class %s of school %s' %
                                       (sub, standard, school.school_name))
                            except Exception as e:
                                print ('failed in creating the scheme of subject %s of class %s of school %s' %
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

    maths_stream = ['English', 'Mathematics', 'Physics', 'Chemistry']
    biology_stream = ['English', 'Biology', 'Physics', 'Chemistry']
    commerce_stream = ['English', 'Economics', 'Accountancy', 'Business Studies']
    humanities_stream = ['English', 'Socialogy', 'History', 'Economics']
    maths = 'Mathematics'
    bio = 'Biology'
    commerce = 'Commerce'
    humanities = 'Humanities'

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
                    print ('Successfully got hold of sheet! the chako')
                for row in range(sheet.nrows):
                    # get the subject name
                    if row != 0:
                        erp = str(sheet.cell(row, 1).value)
                        print(erp)
                        try:
                            student = Student.objects.get(school=school, student_erp_id=erp)
                            student_name = '%s %s' % (student.fist_name, student.last_name)

                            stream = (sheet.cell(row, 5).value).title()

                            print('stream chosen by %s is %s' % (student_name, stream))
                            if stream == maths:
                                print('going to set the chosen_stream to be %s' % stream)
                                chosen_stream = list(maths_stream)
                                print('chosen_stream = Mathematics')
                                try:
                                    m_stream = Stream.objects.get(stream='Mathematics')
                                    stream_mapping = StreamMapping.objects.get_or_create(student=student,
                                                                                         stream=m_stream)
                                    print('set Mathematics for %s' % student)
                                    print(stream_mapping)
                                except Exception as e:
                                    print('failed to create %s stream mapping for %s' % (stream, student))
                                    print('exception 08062019-A from exam views.py %s %s' % (e.message, type(e)))

                            if stream == bio:
                                print('going to set the chosen_stream to be %s' % stream)
                                chosen_stream = list(biology_stream)
                                print('chosen_stream = Biology')
                                try:
                                    b_stream = Stream.objects.get(stream='Biology')
                                    stream_mapping = StreamMapping.objects.get_or_create(student=student,
                                                                                         stream=b_stream)
                                    print('set biology for %s' % student)
                                    print(stream_mapping)
                                except Exception as e:
                                    print('failed to create %s stream mapping for %s' % (stream, student))
                                    print('exception 08062019-B from exam views.py %s %s' % (e.message, type(e)))

                            if stream == commerce:
                                print('going to set the chosen_stream to be %s' % stream)
                                chosen_stream = list(commerce_stream)
                                print('chosen_stream = Commerce')
                                try:
                                    c_stream = Stream.objects.get(stream='Commerce')
                                    stream_mapping = StreamMapping.objects.get_or_create(student=student,
                                                                                         stream=c_stream)
                                    print('set Commerce for %s' % student)
                                    print(stream_mapping)
                                except Exception as e:
                                    print('failed to create %s stream mapping for %s' % (stream, student))
                                    print('exception 08062019-C from exam views.py %s %s' % (e.message, type(e)))

                            if stream == humanities:
                                print('going to set the chosen_stream to be %s' % stream)
                                chosen_stream = list(humanities_stream)
                                print('chosen_stream = Humanities')
                                try:
                                    h_stream = Stream.objects.get(stream='Humanities')
                                    stream_mapping = StreamMapping.objects.get_or_create(student=student,
                                                                                         stream=h_stream)
                                    print('set Humanities for %s' % student)
                                    print(stream_mapping)
                                except Exception as e:
                                    print('failed to create %s stream mapping for %s' % (stream, student))
                                    print('exception 08062019-D from exam views.py %s %s' % (e.message, type(e)))

                            elective = (sheet.cell(row, 6).value).title()
                            print('elective chosen by %s is %s' % (student_name, elective))

                            try:
                                chosen_stream.append(str(elective))
                                print('complete list of subjects to be mapped for %s' % student_name)
                                print(chosen_stream)
                            except Exception as e:
                                print('failed to add elective %s to chosen stream' % elective)
                                print('exception 28122018-A from exam views.py %s %s' % (e.message, type(e)))

                            print('setting stream %s  & elective %s for %s' % (stream, elective, student_name))
                            for sub in chosen_stream:
                                try:
                                    subject = Subject.objects.get(school=school, subject_name=sub)
                                    print('retrieved the subject object for %s' % sub)
                                    mapping = HigherClassMapping.objects.get(student=student, subject=subject)
                                    print ('subject %s mapping for %s already exist. Not doing again.' % (
                                        sub, student_name))
                                except Exception as e:
                                    print ('exception 141117-C from exam views.py %s %s' % (e.message, type(e)))
                                    print ('subject %s mapping for %s does not exist. Hence creating...' % (
                                        sub, student_name))
                                    try:
                                        mapping = HigherClassMapping(student=student, subject=subject)
                                        mapping.save()
                                        print ('created %s subject mapping for % s' % (sub, student_name))
                                    except Exception as e:
                                        print ('exception 141117-D from exam views.py %s %s' % (e.message, type(e)))
                                        print ('failed to create %s subject mapping for %s' % (sub, student_name))
                        except Exception as e:
                            print ('failed to create subject mapping')
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
                    erp_id = sheet.cell(row, 1).value
                    print(erp_id)
                    try:
                        student = Student.objects.get(school=school, student_erp_id=erp_id)
                        print ('now dealing with %s %s' % (student.fist_name, student.last_name))
                    except Exception as e:
                        print ('student with erp id %s does not exist' % erp_id)
                        print ('exception 231017-G from exam views.py %s %s ' % (e.message, type(e)))
                        continue

                    # 31/10/2017 - get the third language
                    t_l = sheet.cell(row, 5).value
                    print('third language specified for %s %s in the sheet is %s' %
                          (student.fist_name, student.last_name, t_l))
                    try:
                        third_lang = Subject.objects.get(school=school, subject_name=t_l)
                    except Exception as e:
                        print('Exception 311017-A from exam views.py %s %s' % (e.message, type(e)))
                        print('%s is not a third languate!' % t_l)

                    try:
                        record = ThirdLang.objects.get(student=student)
                        print('third language for %s %s is already set as %s. This will be updated' %
                              (student.fist_name, student.last_name, record.third_lang.subject_name))
                        print ('third language ' + student.fist_name + ' ' +
                               student.last_name + ' already exists. This will be updated')
                        try:
                            record.third_lang = third_lang
                            record.save()
                            print('successfully updated third language for %s %s as %s' %
                                  (student.fist_name, student.last_name, t_l))
                            print ('successfully updated the third language for ' +
                                   student.fist_name, ' ' + student.last_name)
                        except Exception as e:
                            print ('failed to update the third language for ' +
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
    school = School.objects.get(id=school_id)
    school_name = school.school_name
    school_address = school.school_address
    print(school)
    standard = Class.objects.get(school=school, standard=the_class)
    print(standard)
    sec = Section.objects.get(school=school, section=section)
    print(sec)

    # 07/04/2019 - get the start position for school name and address to appear on the top
    try:
        ms = Marksheet.objects.get(school=school)
        title_start = ms.title_start
        address_start = ms.address_start
        place = ms.place
        result_date = ms.result_date
        logo_left = ms.logo_left_margin
        logo_width = ms.logo_width
        affiliation = ms.affiliation
        board_logo_path = ms.board_logo_path
        print('board_logo_path = %s' % board_logo_path)
    except Exception as e:
        print('failed to retrieve the start coordinates for school name and address %s ' % school.school_name)
        print('exception 07022019-A from exam view.py %s %s' % (e.message, type(e)))
        title_start = 130
        address_start = 155

    # 04/01/2018 get the logos
    try:
        conf = Configurations.objects.get(school=school)
        short_name = conf.school_short_name
    except Exception as e:
        print('failed to retrieve the short name for %s' % school_name)
        print('exception 04022018-A from exam views.py %s %s' % (e.message, type(e)))

    wings = get_wings(school)
    junior_classes = wings['junior_classes']
    middle_classes = wings['middle_classes']
    ninth_tenth = wings['ninth_tenth']
    higher_classes = wings['higher_classes']

    if request.method == 'GET':
        print(request.body)
        whole_class = request.GET.get('whole_class')
        print(whole_class)
        selected_student = request.GET.get('selected_student')
        print (selected_student)

        if whole_class == 'true':
            pdf_name = '%s-%s%s' % (the_class, section, '_Term2_Results.pdf')
            # pdf_name = the_class + '-' + section + '_Term1_Results.pdf'
        else:
            adm_no = selected_student.partition('(')[-1].rpartition(')')[0]
            print('admission/registrtion no is %s' % adm_no)
            s = Student.objects.get(school=school, student_erp_id=adm_no)
            print(s)
            selected_student = ('%s_%s' % (s.fist_name, s.last_name))
            print('selected_student now = %s' % selected_student)
            pdf_name = ('%s_%s_TermI_Results.pdf' % (s.fist_name, s.last_name))
            print('pdf_name = %s' % pdf_name)
        print('pdf file generated will be %s' % pdf_name)

        response = HttpResponse(content_type='application/pdf')
        content_disposition = ('attachment; filename= %s' % pdf_name)
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
            storage_client = storage.Client()
            bucket = storage_client.get_bucket('classup')
            print(bucket)
            # cbse_logo_path = 'classup2/media/dev/cbse_logo/Logo/cbse-logo.png'
            blob = bucket.blob(board_logo_path)
            # blob.download_to_filename('exam/cbse_logo.png')
            blob.download_to_filename('exam/board_logo.png')
            # cbse_logo = Image.open('exam/cbse_logo.png')
            # blob.download_to_filename('exam/cbse_logo.png')
            board_logo = Image.open('exam/board_logo.png')
            print('board logo downloaded')

            school_logo_path = 'classup2/media/dev/school_logos/%s/%s.png' % (short_name, short_name)
            blob = bucket.blob(school_logo_path)
            blob.download_to_filename('exam/%s.png' % short_name)
            school_logo = Image.open('exam/%s.png' % short_name)
            print('school logo downloaded')

            logo_url = 'https://storage.googleapis.com/classup/classup2/media/dev/school_logos/%s/%s.png' % \
                       (short_name, short_name)
            print('logo_url = %s' % logo_url)

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
                      ('ALIGN', (1, 0), (8, 0), 'CENTER'),
                      ('ALIGN', (10, 0), (11, 0), 'CENTER'),
                      ('SPAN', (1, 0), (8, 0)),
                      ('SPAN', (9, 0), (12, 0)),
                      ('SPAN', (3, 1), (5, 1)),
                      ('SPAN', (6, 1), (8, 1)),
                      ('LINEABOVE', (0, 1), (0, 1), 1, colors.white),
                      ('LINEABOVE', (0, 2), (0, 2), 1, colors.white),
                      ('FONTSIZE', (0, 0), (-1, -1), 7),
                      ('FONT', (0, 0), (11, 0), 'Times-Bold'),
                      ('FONT', (0, 1), (11, 1), 'Times-Bold'),
                      ('FONT', (0, 2), (11, 2), 'Times-Bold'),
                      ('FONT', (0, 2), (11, 1), 'Times-Bold')
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
            # style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            #           ('BOX', (0, 0), (-1, -1), 1, colors.black),
            #           ('TOPPADDING', (0, 0), (-1, -1), 1),
            #           ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            #           ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            #           ('ALIGN', (1, 0), (6, 0), 'CENTER'),
            #           ('ALIGN', (7, 0), (12, 0), 'CENTER'),
            #           ('SPAN', (1, 0), (6, 0)),
            #           ('SPAN', (7, 0), (12, 0)),
            #           ('FONTSIZE', (0, 0), (-1, -1), 7),
            #           ('FONT', (0, 0), (12, 0), 'Times-Bold'),
            #           ('FONT', (0, 1), (0, 1), 'Times-Bold')]

            # 29/09/2019 - uncomment when generating result for final exam
            # style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            #           ('BOX', (0, 0), (-1, -1), 1, colors.black),
            #           ('TOPPADDING', (0, 0), (-1, -1), 1),
            #           ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            #           ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            #           ('ALIGN', (1, 0), (7, 0), 'CENTER'),
            #           ('ALIGN', (8, 0), (14, 0), 'CENTER'),
            #           ('SPAN', (1, 0), (7, 0)),
            #           ('SPAN', (8, 0), (14, 0)),
            #           ('FONTSIZE', (0, 0), (-1, -1), 7),
            #           ('FONT', (0, 0), (13, 0), 'Times-Bold'),
            #           ('FONT', (0, 1), (0, 1), 'Times-Bold')]

            # 29/09/2019 - comment when generating results for fianl exam
            style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                      ('BOX', (0, 0), (-1, -1), 1, colors.black),
                      ('TOPPADDING', (0, 0), (-1, -1), 1),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                      ('ALIGN', (1, 0), (7, 0), 'CENTER'),
                      ('SPAN', (1, 0), (7, 0)),

                      ('FONTSIZE', (0, 0), (-1, -1), 7),
                      ('FONT', (0, 0), (7, 0), 'Times-Bold'),
                      ('FONT', (0, 1), (0, 1), 'Times-Bold')]
            # 29/09/2019  - uncomment when generating result for final exam
            # style2 = style3 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            #                     ('BOX', (0, 0), (-1, -1), 1, colors.black),
            #                     ('TOPPADDING', (0, 0), (-1, -1), 1),
            #                     ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            #                     ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            #                     ('ALIGN', (0, 0), (1, 0), 'RIGHT'),
            #                     ('ALIGN', (2, 0), (3, 0), 'RIGHT'),
            #                     ('SPAN', (0, 0), (1, 0)),
            #                     ('SPAN', (2, 0), (3, 0)),
            #                     ('FONTSIZE', (0, 0), (-1, -1), 8),
            #                     ('FONT', (0, 0), (1, 0), 'Times-Bold'),
            #                     ('FONT', (2, 0), (3, 0), 'Times-Bold')]

            # 29/09/2019 - comment while generating result for final exam
            style2 = style3 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                               ('BOX', (0, 0), (-1, -1), 1, colors.black),
                               ('TOPPADDING', (0, 0), (-1, -1), 1),
                               ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                               ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                               ('ALIGN', (0, 0), (1, 0), 'RIGHT'),
                               ('SPAN', (0, 0), (1, 0)),
                               ('FONTSIZE', (0, 0), (-1, -1), 8),
                               ('FONT', (0, 0), (1, 0), 'Times-Bold')]
        if the_class in ninth_tenth:
            print('result being prepared for class %s, hence only final Term Results will be prepared' % the_class)
            style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                      ('BOX', (0, 0), (-1, -1), 1, colors.black),
                      ('TOPPADDING', (0, 0), (-1, -1), 1),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                      ('ALIGN', (1, 0), (7, 0), 'CENTER'),
                      ('SPAN', (1, 0), (7, 0)),
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
        session = 'Academic Session 2019-20'
        adm_no_lbl = 'Admission No:'
        stu_name_lbl = 'Student Name:'
        father_name_lbl = 'Mother/Father Name:'
        dob_lbl = 'Date of Birth:'
        class_sec_lbl = 'Class/Section:'

        sub_dict = {}

        left_margin = -30

        def marksheet(c, s):
            c.translate(inch, inch)
            c.drawInlineImage(school_logo, logo_left, 690, width=logo_width, height=50)
            c.drawInlineImage(board_logo, left_margin, 690, width=60, height=50)
            font = 'Times-Bold'
            c.setFont(font, 14)

            c.drawString(title_start, top + 20, school_name)
            c.setFont(font, 10)
            c.drawString(address_start, top + 7, school_address)
            c.setFont(font, 8)
            c.drawString(180, top - 4, '(%s)' % affiliation)
            c.setFont(font, 10)
            c.line(-30, line_top, 6.75 * inch, line_top)

            c.setFont(font, 10)
            c.drawString(152, session_top + 2, session)
            print('heading created')

            # heading = 'Performance Analysis Sheet '
            # c.drawString(146, report_card_top + 2, heading)

            c.setFont(font, 10)
            c.drawString(left_margin, stu_detail_top, adm_no_lbl)
            c.drawString(tab, stu_detail_top, s.student_erp_id)

            c.drawString(left_margin, stu_detail_top - 15, stu_name_lbl)
            c.drawString(tab, stu_detail_top - 15, s.fist_name + ' ' + s.last_name)
            c.drawString(left_margin + 300, stu_detail_top - 15, class_sec_lbl)
            # c.drawString(left_margin, stu_detail_top - 60, class_sec_lbl)
            c.drawString(left_margin + 300 + tab, stu_detail_top - 15, the_class + '-' + section)

            c.drawString(left_margin, stu_detail_top - 30, father_name_lbl)

            # 19/03/2018 We need to show both mother & father's name
            try:
                additional_details = AdditionalDetails.objects.get(student=s)
                mother_name = additional_details.mother_name
            except Exception as e:
                print('exception 19032018-A from exam views.py %s %s' % (e.message, type(e)))
                print('failed to retrieve mother name for %s %s' % (s.fist_name, s.last_name))
                mother_name = ' '
            if mother_name == ' ':
                if 'Mr.' not in s.parent.parent_name:
                    parent_name = 'Mr. %s' % s.parent.parent_name
                else:
                    parent_name = s.parent.parent_name
            else:
                if 'Mr.' not in s.parent.parent_name:
                    parent_name = '%s / Mr. %s' % (mother_name, s.parent.parent_name)
                else:
                    parent_name = '%s / %s' % (mother_name, s.parent.parent_name)
            c.drawString(tab, stu_detail_top - 30, parent_name)

            # c.drawString(left_margin, stu_detail_top - 45, dob_lbl)
            c.drawString(left_margin + 300, stu_detail_top, dob_lbl)
            try:
                d = DOB.objects.get(student=s)
                dob = d.dob
                print(dob)
                # c.drawString(tab, stu_detail_top - 45, dob.strftime('%d-%m-%Y'))
                c.drawString(left_margin + tab + 300, stu_detail_top, dob.strftime('%d-%m-%Y'))
            except Exception as e:
                print ('date of birth not yet set for %s %s ' % (s.fist_name, s.last_name))
                print('Exception 23102017-A from exam views.py %s %s ' % (e.message, type(e)))

            print('report heading prepared')

            # # 06/02/2019 - calculate the attendance
            # att_taken_t1 = AttendanceTaken.objects.filter(date__gte='2018-04-01', date__lte='2018-10-30',
            #                                               the_class=s.current_class, section=s.current_section).count()
            # print('total working days in term I = %i' % att_taken_t1)
            #
            # att_taken_t2 = AttendanceTaken.objects.filter(date__gte='2018-11-01', date__lte='2019-03-15',
            #                                               the_class=s.current_class, section=s.current_section).count()
            # print('total working days in term II = %i' % att_taken_t2)

            c.setFont(font, 8)
            if the_class in higher_classes:
                print('result being prepared for class %s. This will be in school own format' % the_class)

                # data1 = [['', 'TERM RESULT', '', '', '', '', '', '', '', '', 'CUMULATIVE RESULT', '', '', ''],
                #          ['\nSUBJECT', 'UT-I', 'UT-II', 'UT-III', 'Half Yearly\nExam', '', '',
                #            'Final Exam', '', '', 'Unit\nTest', 'Half Yearly\nExam', 'Final\nExam', 'Total'],
                #          ['', '25', '25', '25', 'Th', 'Pr', 'Tot', 'Th', 'Pr', 'Tot', '25', '25', '50', '100']]

                data1 = [['', 'TERM RESULT', '', '', '', '', '', '', 'CUMULATIVE RESULT', '', '', ''],
                         ['\nSUBJECT', 'UT-I', 'UT-II', 'Half Yearly\nExam', '', '',
                          'Final Exam', '', '', 'Unit\nTest', 'Half Yearly\nExam', 'Final\nExam', 'Total'],
                         ['', '25', '25', 'Th', 'Pr', 'Tot', 'Th', 'Pr', 'Tot', '25', '25', '50', '100']]
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
                humanties_stream = ['English', 'History', 'Sociology', 'Economics']

                try:
                    print('now determining the stream chosen by %s %s...' % (s.fist_name, s.last_name))
                    if 'Mathematics' in sub_dict.values():
                        chosen_stream = maths_stream
                        print('%s %s has chosen %s stream' % (s.fist_name, s.last_name, 'maths'))
                    if 'Biology' in sub_dict.values():
                        chosen_stream = bio_stream
                        print('%s %s has chosen %s stream' % (s.fist_name, s.last_name, 'biology'))
                    if 'Accountancy' in sub_dict.values():
                        chosen_stream = commerce_stream
                        print('%s %s has chosen %s stream' % (s.fist_name, s.last_name, 'commerce'))
                    if 'History' in sub_dict.values():
                        chosen_stream = humanties_stream
                        print('%s %s has chosen %s stream' % (s.fist_name, s.last_name, 'humanities'))
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

                unit_exams = Exam.objects.filter(school=school, start_class='XI', exam_type='unit')
                term_exams = Exam.objects.filter(school=school, start_class='XI', exam_type='term')

                try:
                    for sub in chosen_stream:
                        sub_row = [sub]
                        print('sub_row at this stage = ')
                        print(sub_row)
                        print('now retrieving all test marks for %s %s in %s' % (s.fist_name, s.last_name, sub))
                        subject = Subject.objects.get(school=school, subject_name=sub)
                        ut_total = 0.0
                        for a_unit_exam in unit_exams:
                            try:
                                test = ClassTest.objects.get(subject=subject, the_class=standard,
                                                             section=sec, exam=a_unit_exam)
                                print('test was conducted for %s under exam: %s for class %s' %
                                      (sub, a_unit_exam, the_class))
                                print(test)
                                result = TestResults.objects.get(class_test=test, student=s)
                                marks = float(result.marks_obtained)

                                if marks < 0.0:
                                    marks = 'ABS'
                                else:
                                    if float(test.max_marks) != 25.0:
                                        print('max marks for %s in %s were %f. Conversion is required' %
                                              (sub, a_unit_exam.title, float(test.max_marks)))
                                        marks = round((25 * marks) / float(test.max_marks), 2)

                                        ut_total = ut_total + marks
                                sub_row.append(marks)
                            except Exception as e:
                                print('exception 15022019-A from exam views.py %s %s' % (e.message, type(e)))
                                print('unit test for %s not created for %s' % (a_unit_exam, subject))
                        index = 0
                        for a_term_exam in term_exams:
                            try:
                                test = ClassTest.objects.get(subject=subject, the_class=standard,
                                                             section=sec, exam=a_term_exam)
                                result = TestResults.objects.get(class_test=test, student=s)
                                marks = float(result.marks_obtained)
                                if marks < 0.0:
                                    marks = 'ABS'

                                term_test_results = TermTestResult.objects.get(test_result=result)

                                # this is a half yearly or annual exam. The possibility of practical marks...
                                if subject.subject_prac:
                                    # if sub in prac_subjects:
                                    print('%s has practical component' % (sub))
                                    prac_marks = float(term_test_results.prac_marks)
                                    if prac_marks < 0.0:
                                        #     if index == 0 and subject.subject_name in commerce_sub:
                                        #         prac_marks = 'NA'
                                        #     else: 888
                                        prac_marks = ' '
                                        tot_marks = marks
                                    else:
                                        # 26032018 - there is a possibility that student was absent
                                        # in theory but present in practical
                                        if marks != 'ABS':
                                            # if subject.subject_name not in commerce_sub:
                                            #     tot_marks = marks + prac_marks
                                            # else:
                                            #     if index == 0:
                                            #         tot_marks = marks
                                            #     else:
                                            tot_marks = marks + prac_marks
                                        else:
                                            tot_marks = prac_marks
                                else:
                                    print('%s does not have practical component' % (sub))
                                    prac_marks = 'NA'
                                    tot_marks = marks
                                sub_row.append(marks)
                                sub_row.append(prac_marks)
                                sub_row.append(tot_marks)

                                if index == 0:  # we are dealing with half-yearly exam
                                    print('dealing with half yearly exam')
                                    # 20/02/2019 only theory marks will be considered in the cumulative
                                    # if subject.subject_prac:
                                    # # if sub in prac_subjects:
                                    #     if subject.subject_name not in commerce_sub:
                                    #         #half_yearly_marks = tot_marks - prac_marks
                                    #         half_yearly_marks = marks
                                    #     else:
                                    #         half_yearly_marks = tot_marks
                                    # else:
                                    #     half_yearly_marks = tot_marks
                                    half_yearly_marks = tot_marks
                                    print('half yearly marks =')
                                    print(half_yearly_marks)
                                if index == 1:  # we are dealing with final exam
                                    print('dealing with final exam')
                                    if subject.subject_prac:
                                        # if sub in prac_subjects:
                                        final_marks = tot_marks - prac_marks
                                    else:
                                        final_marks = tot_marks
                                    print('final marks = ')
                                    print(final_marks)
                                # index += 1
                            except Exception as e:
                                print('exception 15022019-B from exam views.py %s %s' % (e.message, type(e)))
                                print('term test for %s not created for %s' % (a_term_exam, subject))
                                for component in ['Th', 'Prac', 'Total']:
                                    sub_row.append(' ')
                                # index += 1
                            index += 1

                        # calculate the cumulative result for this subject. UTs & Half yearly weightage is 25% each
                        #  & final exam weightage is 50%
                        grand_total = 0.0
                        try:
                            ut_cumul = round(ut_total / float(2), 2)
                            grand_total += ut_cumul
                            # 29/09/2019 - uncomment when preparing result for final exam
                            sub_row.append(ut_cumul)

                            # 20/02/2019 cumulative for half yearly to be calculated out of 70 if the subject
                            # has practical component
                            # if sub in prac_subjects:
                            commerce_sub = ['Economics', 'Accountancy', 'Business Studies']
                            if half_yearly_marks != 'ABS':
                                # if subject.subject_name not in commerce_sub:
                                #     half_year_cumul = round((half_yearly_marks*float(25))/float(subject.theory_marks), 2)
                                # else:
                                half_year_cumul = round((half_yearly_marks * float(25)) / 100.00, 2)
                                grand_total += half_year_cumul
                            else:
                                half_year_cumul = 'ABS'
                            # else:
                            #     half_year_cumul = round(half_yearly_marks/float(4), 2)

                            # 29/09/2019 - uncomment when preparing result for final exam
                            sub_row.append(half_year_cumul)

                            if final_marks != 'ABS':
                                final_cumul = round(final_marks * float(50) / float(subject.theory_marks), 2)
                                grand_total += final_cumul
                            else:
                                final_cumul = 'ABS'

                            # 29/09/2019 - uncomment while generating result for final exam
                            # sub_row.append(final_cumul)
                            # grand_total = ut_cumul + half_year_cumul + final_cumul
                            # sub_row.append(grand_total)
                        except Exception as e:
                            print('failed to enter Cumulative Result. This may be because certain marks not entered')
                            print('exception 01032018-A from exam views.py %s %s' % (e.message, type(e)))
                        data1.append(sub_row)
                        print('data1 = ')
                        print(data1)
                    table1 = Table(data1)
                    table1.setStyle(TableStyle(style1))
                    table1.wrapOn(c, left_margin, 0)
                    print('everything was ok upto this point')
                    table1.drawOn(c, left_margin, table1_top)
                    print('table1 drawn for %s %s' % (s.fist_name, s.last_name))
                    theory_prac_split = ms.theory_prac_split
                    print('theory_prac_split = %s' % theory_prac_split)
                    c.drawString(left_margin, table1_top - 20, theory_prac_split)
                    split_2 = ms.split_2
                    c.drawString(left_margin, table1_top - 30, split_2)
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
                    except Exception as e:
                        print('failed to retrieve %s Co-scholastic grades for %s %s for ' %
                              ('Term2', s.fist_name, s.last_name))
                        print('exception 20032017-X from exam views.py %s %s' % (e.message, type(e)))
                except Exception as e:
                    print('failed to retrieve Co-scholastic grades for %s %s for ' % (s.fist_name, s.last_name))
                    print('exception 07022018-Z from exam views.py %s %s' % (e.message, type(e)))

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
                    print('%s is in middle classes' % the_class)
                    end_class = 'VIII'
                    # 29/09/2019 - uncomment when generting final exam result
                    # data1 = [['Scholastic\nAreas', 'Term-1 (100 Marks)', '', '', '', '', '', '',
                    #           'Term-2 (100 Marks)', '', '', '', '', '', ''],
                    #          ['Sub Name', 'Per\n Test\n(5)', 'Mult\nAssess\n(5)', 'Portfolio\n(5)', 'Sub\nEnrich\n(5)',
                    #           'Half\nYearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade',
                    #           'Per\n Test\n(5)', 'Mult\nAssess\n(5)', 'Portfolio\n(5)', 'Sub\nEnrich\n(5)',
                    #           'Yearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade']]

                    # 29/09/2019 - comment when generating final exam result
                    data1 = [['Scholastic\nAreas', 'Term-1 (100 Marks)', '', '', '', '', '', ''],
                             ['Sub Name', 'Per\n Test\n(5)', 'Mult\nAssess\n(5)', 'Portfolio\n(5)', 'Sub\nEnrich\n(5)',
                              'Half\nYearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade']]
                if the_class in ninth_tenth:
                    end_class = 'X'
                    data1 = [['Scholastic\nAreas', 'Academic Year (100 Marks)', '', '', '', '', '', ''],
                             ['Sub Name', 'Per Test\n(5)', 'Multi\nAssess\n(5)',
                              'Portfolio\n(5)', 'Sub\nEnrich\n(5)',
                              'Half\nYearly Exam\n(80)', 'Marks\nObtained\n(100)', 'Grade']]
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
                    terms = Exam.objects.filter(school=school, exam_type='term', end_class=end_class)
                    try:
                        for idx, term in enumerate(terms):
                            print(term)
                            # for class IX, only the result of Term2, ie the final exam is to be shown
                            # if term == 'Term1' and the_class in ninth_tenth:
                            # continue

                            # exam =  Exam.objects.get(school=school, title=term)
                            # print(exam)
                            # if idx == 0 and the_class in ninth_tenth and school_id == 20:
                            #     continue
                            try:
                                if sub.subject_name not in ['GK', 'Moral Science', 'Drawing']:
                                    test = ClassTest.objects.get(subject=sub, the_class=standard,
                                                                 section=sec, exam=term)
                                    print(test)
                                    tr = TestResults.objects.get(class_test=test, student=s)

                                if sub.subject_name in ['GK', 'Moral Science', 'Drawing']:
                                    test = ClassTest.objects.filter(subject=sub,
                                                                    the_class=standard, section=sec)[idx]

                                    tr = TestResults.objects.get(class_test=test, student=s)
                                    pa = 'NA'
                                    multi_assess = 'NA'
                                    sub_enrich = 'NA'
                                    main = 'NA'
                                    notebook = 'NA'
                                    if sub.subject_name == 'GK':
                                        total = 'NA'
                                        grade = tr.grade
                                else:
                                    ttr = TermTestResult.objects.get(test_result=tr)
                                    pa = round(ttr.periodic_test_marks)
                                    multi_assess = ttr.multi_asses_marks

                                    notebook = ttr.note_book_marks
                                    sub_enrich = ttr.sub_enrich_marks
                                    main = tr.marks_obtained

                                    # 03/12/2019 - for Lord Krishna Public school, for classes III to VIII
                                    # max marks were 80 and for classes I & II max marks were from 50.
                                    # These need to be converted to be from 80. Only for term I
                                    if school_name == 'Lord Krishna Public School':
                                        if the_class in ['III', 'IV', 'V', 'VI', 'VII', 'VIII']:
                                            # main = float(main) * 1.14
                                            main = float(main) * 1.0
                                        if the_class in ['I', 'II']:
                                            main = float(main) * 1.6
                                    total = float(main) + float(pa) + float(multi_assess) + float(notebook) + float(
                                        sub_enrich)
                                    print(total)

                                    if the_class in ninth_tenth:
                                        if school_name == 'Jagran Public School':
                                            print('the_class in ninth_tenth and school is Jagran Public School')
                                            if sub.subject_name == 'Computer':
                                                print('suject is computer')
                                                pa = 'NA'
                                                multi_assess = 'NA'
                                                sub_enrich = 'NA'
                                                main = tr.marks_obtained
                                                notebook = 'NA'
                                                ttr = TermTestResult.objects.get(test_result=tr)
                                                theory = tr.marks_obtained
                                                prac = ttr.prac_marks
                                                total = float(theory) + float(prac)
                                        else:
                                            print('this is not Jagran Public School')
                                    # in case the student was absent we need to show ABS in the marksheet.
                                    if the_class not in ninth_tenth:
                                        if float(main) < 0.0:
                                            main = 'ABS'
                                            total = float(pa) + float(multi_assess) + float(notebook) + float(
                                                sub_enrich)
                                        grade = get_grade(total)
                                        print('grade obtained by %s in %s exam of %s: %s' %
                                              (s.fist_name, term, sub.subject_name, grade))
                                    if the_class in ninth_tenth:
                                        if sub.subject_name == 'Computer':
                                            if school_id == 23:
                                                main = 'NA'
                                    grade = get_grade(total)
                                if total > -1000.0:
                                    sub_row.append(pa)
                                    sub_row.append(multi_assess)
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
                        # 29/09/2019- uncomment when generating result for final exam
                        # data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale]', '',
                        #         'Co-Scholastic Areas: Term-2[On a 3-point(A-C) grading scale]', '']]

                        # 29/09/2019 - comment while generating result for final exam
                        data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale]', '']]
                    if the_class in ninth_tenth:
                        data2 = [['Co-Scholastic Areas: Academic Year[On a 3-point(A-C) grading scale]', '']]
                    work_array = []
                    art_array = []
                    health_array = []
                    dscpln_array = []

                    # 29/09/2019 - uncomment while generating result for final exam
                    # terms = ['term1', 'term2']

                    # 29/09/2019 - comment while generating result for final exam
                    terms = ['term1']
                    if the_class in ninth_tenth:
                        # 29/09/2019 - uncomment while generating result for final exam
                        # terms = ['term2']
                        # 29/09/2019 - comment while generating result for final exam
                        terms = ['term1']

                    for term in terms:
                        # for class IX, only the result of Term2, ie the final exam is to be shown
                        # if term == 'Term1' and the_class in ninth_tenth:
                        # continue
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
                        # 29/09/2019 - uncomment while generating result for final exam
                        # data3 = [['Grade', '', 'Grade', '']]

                        # 29/09/2019 - comment while generating result for final exam
                        data3 = [['Grade', '']]
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
                    if ms.show_attendance:
                        c.drawString(left_margin, table3_top - 25, 'Attendance: ')
                        try:
                            attendance = IndividualAttendance.objects.get(student=s)
                            total_days = attendance.total_days
                            present_days = attendance.present_days
                            # c.drawString(left_margin + 50, table3_top - 25, '%s/%s' % (str(present_days),
                            #                                                              str(total_days)))
                        except Exception as e:
                            print('exception 28092019-A from exam views.py %s %s' % (e.message, type(e)))
                            print('attendance recored not available for %s' % s)

                    if the_class not in ninth_tenth:
                        c.drawString(left_margin, table3_top - 35, 'Promoted to Class: ')
                        promoted_status = 'N/A'
                        # get the class to which this student is promoted. Only if he has passed the exam
                        # try:
                        #     not_promoted = NPromoted.objects.get(student=s)
                        #     print('student %s %s has failed in class %s.' % (s.fist_name, s.last_name, the_class))
                        #     print(not_promoted)
                        #     promoted_status = 'Not Promoted. %s' % not_promoted.details
                        # except Exception as e:
                        #     print('student %s %s has passed in class %s.' % (s.fist_name, s.last_name, the_class))
                        #     print('exception 02032018-A from exam views.py %s %s' % (e.message, type(e)))
                        #     try:
                        #         current_class = Class.objects.get(school=school, standard=the_class)
                        #         next_class_sequence = current_class.sequence + 1
                        #         next_class = Class.objects.get(school=school, sequence=next_class_sequence)
                        #         next_class_standard = next_class.standard
                        #         promoted_status = next_class_standard
                        #     except Exception as e:
                        #         print('%s %s of class %s has passed. But failed to determine his next class' %
                        #               (s.fist_name, s.last_name, the_class))
                        #         print('exception 02032018-B from exam views.py %s %s' % (e.message, type(e)))
                        c.drawString(tab - 20, table3_top - 35, promoted_status)

                    c.drawString(left_margin, table3_top - 55, 'Place & Date:')
                    # c.drawString(left_margin + 50, table3_top - 55, 'Noida   26/03/2018')
                    c.drawString(175, table3_top - 55, 'Signature of Class Teacher')
                    c.drawString(400, table3_top - 55, 'Signature of Principal')
                except Exception as e:
                    print('exception 08022018-A from exam views.py %s %s' % (e.message, type(e)))

                # 29/09/2019 - show Grading scheme on next page
                # c.showPage()

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
                if ms.show_attendance:
                    c.drawString(left_margin, table3_top - 25, 'Attendance: ')
                    try:
                        attendance = IndividualAttendance.objects.get(student=s)
                        total_days = attendance.total_days
                        present_days = attendance.present_days
                        # c.drawString(left_margin +50, table3_top - 25, '%s/%s' % (str(present_days), str(total_days)))
                    except Exception as e:
                        print('exception 28092019-B from exam views.py %s %s' % (e.message, type(e)))
                        print('attendance recored not available for %s' % s)
                if the_class in ninth_tenth:
                    c.drawString(left_margin, table3_top - 35, 'Promoted to Class: ')
                else:
                    c.drawString(left_margin, table3_top - 35, 'Promoted to Class: ')
                promoted_status = 'N/A'
                # get the class to which this student is promoted. Only if he has passed the exam
                # try:
                #     not_promoted = NPromoted.objects.get(student=s)
                #     print('student %s %s has failed in class %s.' % (s.fist_name, s.last_name, the_class))
                #     print(not_promoted)
                #     promoted_status = 'Not Promoted. %s' % not_promoted.details
                # except Exception as e:
                #     print('student %s %s has passed in class %s.' % (s.fist_name, s.last_name, the_class))
                #     print('exception 02032018-C from exam views.py %s %s' % (e.message, type(e)))
                #     try:
                #         current_class = Class.objects.get(school=school, standard=the_class)
                #         next_class_sequence = current_class.sequence + 1
                #         next_class = Class.objects.get(school=school, sequence=next_class_sequence)
                #         next_class_standard = next_class.standard
                #         promoted_status = next_class_standard
                #     except Exception as e:
                #         print('%s %s of class %s has passed. But failed to determine his next class' %
                #                 (s.fist_name, s.last_name, the_class))
                #         print('exception 02032018-D from exam views.py %s %s' % (e.message, type(e)))
                c.drawString(tab - 20, table3_top - 35, promoted_status)

                c.drawString(tab - 20, table3_top - 25, '')
                c.drawString(left_margin, table3_top - 55, 'Place & Date:')
                place_date = '%s   %s' % (place, result_date)
                c.drawString(left_margin + 50, table3_top - 55, place_date)
                c.drawString(175, table3_top - 55, 'Signature of Class Teacher')
                c.drawString(400, table3_top - 55, 'Signature of Principal')
            except Exception as e:
                print('exception 08022018-A from exam views.py %s %s' % (e.message, type(e)))
            return

        if whole_class == 'true':
            # get the list of all the students, then get the marks of each test conducted for this exam
            students = Student.objects.filter(school=school, current_class=standard,
                                              current_section=sec, active_status=True)
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

        # 31/10/2018 - delete the downloaded png files for school and cbse logo
        try:
            import os
            os.remove('exam/board_logo.png')
            print('successfully removed cbse_logo.png')
            os.remove('exam/%s.png' % short_name)
            print('successfully removed %s.png' % short_name)
        except Exception as e:
            print('exception 31102018-A from exam views.py %s %s' % (e.message, type(e)))
            print('failed to delete downloaded png files for cbse and school logo')
        return response
    return HttpResponse()


def get_wings(school):
    wings = {

    }
    try:
        jc = Wing.objects.get(school=school, wing='junior_classes')
        junior_classes = ast.literal_eval(jc.classes)
        print('junior_classes for %s are: ' % school)
        print(junior_classes)
    except Exception as e:
        print('exception 26092019-A from exam views.py %s %s' % (e.message, type(e)))
        print('junior_classes not defined for %s' % school)
        junior_classes = ['not defined']
    wings['junior_classes'] = junior_classes

    try:
        mc = Wing.objects.get(school=school, wing='middle_classes')
        print('raw middle_classes retrieved for %s: %s. Will be converted to proper string now' %
              (school, mc.classes))
        middle_classes = ast.literal_eval(mc.classes)
        print('middle_classes for %s are: ' % school)
        print(middle_classes)
    except Exception as e:
        print('exception 26092019-B from exam views.py %s %s' % (e.message, type(e)))
        print('middle_classes not defined for %s' % school)
        middle_classes = ['not defined']
    wings['middle_classes'] = middle_classes

    try:
        nt = Wing.objects.get(school=school, wing='ninth_tenth')
        ninth_tenth = ast.literal_eval(nt.classes)
        print('ninth_tenth for %s are: ' % school)
        print(ninth_tenth)
    except Exception as e:
        print('exception 26092019-C from exam views.py %s %s' % (e.message, type(e)))
        print('ninth_tenth not defined for %s' % school)
        ninth_tenth = ['not defined']
    wings['ninth_tenth'] = ninth_tenth

    try:
        hc = Wing.objects.get(school=school, wing='higher_classes')
        higher_classes = ast.literal_eval(hc.classes)
        print('higher_classes for %s are: ' % school)
        print(higher_classes)
    except Exception as e:
        print('exception 26092019-D from exam views.py %s %s' % (e.message, type(e)))
        print('higher_classes not defined for %s' % school)
        higher_classes = ['not defined']
    wings['higher_classes'] = higher_classes

    return wings


class ResultSheet(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        school_id = request.query_params.get('school_id')
        school = School.objects.get(id=school_id)
        standard = request.query_params.get('the_class')
        the_class = Class.objects.get(school=school, standard=standard)
        sec = request.query_params.get('section')
        section = Section.objects.get(school=school, section=sec)
        print ('result sheet will be generated for %s-%s' % (the_class.standard, section.section))

        wings = get_wings(school)
        junior_classes = wings['junior_classes']
        middle_classes = wings['middle_classes']
        ninth_tenth = wings['ninth_tenth']
        higher_classes = wings['higher_classes']

        excel_file_name = 'Result_Sheet_%s-%s.xlsx' % (str(the_class.standard), str(section.section))
        print('excel_file_name = %s' % excel_file_name)

        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        result_sheet = workbook.add_worksheet("Result Sheet")

        border = workbook.add_format()
        border.set_border()

        fmt = format()
        title = workbook.add_format(fmt.get_title())
        header = workbook.add_format(fmt.get_header())

        cell_normal = workbook.add_format(fmt.get_cell_normal())
        cell_normal.set_border()
        cell_bold = workbook.add_format(fmt.get_cell_bold())
        cell_bold.set_border()
        cell_component = workbook.add_format(fmt.get_cell_component())
        cell_component.set_border()
        cell_center = workbook.add_format(fmt.get_cell_center())
        cell_center.set_border()
        vertical_text = workbook.add_format(fmt.get_vertical_text())
        vertical_text.set_border()
        perc_format = workbook.add_format(fmt.get_perc_format())
        cell_grade = workbook.add_format(fmt.get_cell_grade())
        cell_small = workbook.add_format(fmt.get_cell_small())
        fail_format = workbook.add_format()
        fail_format.set_bg_color('yellow')

        school_name = school.school_name + ' ' + school.school_address
        result_sheet.merge_range('A1:AI1', school_name, title)

        title_text = 'CONSOLIDATED RESULT SHEET (2018-2019) FOR CLASS %s-%s' % \
                     (the_class.standard, section.section)
        print (title_text)
        result_sheet.merge_range('A2:AI2', title_text, title)

        # get the name of the class teacher
        class_teacher = 'N/A'
        try:
            ct = ClassTeacher.objects.get(school=school, standard=the_class, section=section)
            class_teacher = '%s %s' % (ct.class_teacher.first_name, ct.class_teacher.last_name)
            print ('class teacher for class %s-%s is %s' %
                   (the_class.standard, section.section, class_teacher))
        except Exception as e:
            print ('exception 19012018-A from exam views.py %s %s' % (e.message, type(e)))
            print ('class teacher for class %s-%s is not set!' % (the_class.standard, section.section))
        result_sheet.merge_range('A3:AI3', ('CLASS TEACHER: %s' % class_teacher), header)

        row = 3
        col = 0
        result_sheet.set_column(col, col, 3)

        if the_class.standard in higher_classes:
            result_sheet.merge_range(row, col, row + 2, col, 'S No', cell_center)
        else:
            result_sheet.merge_range(row, col, row + 1, col, 'S No', cell_center)
        col += 1
        result_sheet.set_column(col, col, 3)

        if the_class.standard in higher_classes:
            result_sheet.merge_range(row, col, row + 2, col, 'House', vertical_text)
        else:
            result_sheet.merge_range(row, col, row + 1, col, 'House', vertical_text)
        col += 1

        result_sheet.set_column(col, col, 14)

        if the_class.standard in higher_classes:
            result_sheet.merge_range(row, col, row + 2, col, 'Student Name\nAdmission/Reg No', cell_center)
        else:
            result_sheet.merge_range(row, col, row + 1, col, 'Student Name\nAdmission/Reg No', cell_center)
        col += 1

        if the_class.standard not in higher_classes:
            try:
                scheme = Scheme.objects.filter(school=school, the_class=the_class)
                sub_count = scheme.count()
                sub_list = []
                for sc in scheme:
                    sub_list.append(sc.subject.subject_name)
                    print('sub_list = ')
                    print (sub_list)
            except Exception as e:
                print('exception 19102018-A from academics views.py %s (%s)' % (e.message, type(e)))
                print('looks the exam scheme is not yet set for class %s of %s' %
                      (the_class.standard, school_name))

            terms = ['Term I', 'Term II']
            if the_class in ninth_tenth:
                terms = ['Academic Year']
            term_comp = ['Tot', '%', 'Grade', 'Rank']

            try:
                if 'GK' in sub_list:
                    print('GK is a grade based subject. Hence Grand total will exclude GK')
                    total_marks = (sub_count - 1) * 100
                else:
                    total_marks = sub_count * 100
                print('the scheme for this class %s consist of %i subjects. Hence total marks = %s' %
                      (the_class.standard, sub_count, str(total_marks)))
                if the_class.standard not in ninth_tenth:
                    term1_heading = 'Term I (%s)' % str(total_marks)
                    term2_heading = 'Term II (%s)' % str(total_marks)
                else:
                    term1_heading = 'Academic Year (%s)' % str(total_marks)
                    term2_heading = ''

                print('Term I heading = %s, Term II heading = %s' % (term1_heading, term2_heading))

                # 19/10/2018 - we have decided to show the components vertically to avoid horizontal scrolling
                # each term width will be the number of subjects plus Term total components
                term_width = sub_count * 2
                print('term width for class % s without taking Third Language or GK into account: %i' %
                      (the_class.standard, term_width))

                if 'Third Language' in sub_list:  # third language need additional column to show third language
                    print('Third Language is present in the scheme of class %s. Hence incrementing term_width' %
                          the_class.standard)
                    term_width += 1
                    print('now, the term_width for class %s: %i' % (the_class.standard, term_width))
                else:
                    print('Third Language is not included in the scheme of class %s. No change in term_width' %
                          the_class.standard)

                if 'GK' in sub_list:
                    print('GK is present in the scheme of class %s. Hence decrementing term_width' %
                          the_class.standard)
                    term_width -= 1

                print('finally, the term_width for class %s: %i' % (the_class.standard, term_width))
                print('for %i subjects, term width will be %i' % (sub_count, term_width))
                print('current column is at %i' % col)
                result_sheet.merge_range(row, col, row, col + term_width - 1, term1_heading, cell_center)
                result_sheet.merge_range(row, col + term_width + len(term_comp), row,
                                         (col + (2 * term_width)) + len(term_comp) - 1, term2_heading, cell_center)
                result_sheet.set_column(col, (term_width * 2) + 15, 2.5)
                row += 1
            except Exception as e:
                print('exception 14102018-A-A from academics views.py %s (%s)' % (e.message, type(e)))
                print('failed to set up Term headings for class %s of %s' %
                      (the_class.standard, school_name))

            print('after setting the term heading we are at %i row' % row)
            for term in terms:
                for sub in sub_list:
                    if sub != 'GK':
                        if sub == 'Third Language':
                            # 19/10/2018 - we are going to show the third language subject in vertical
                            result_sheet.set_column(col, col + 1, 3)
                            result_sheet.merge_range(row, col, row, col + 2, sub, cell_center)
                            col += 3
                        else:
                            result_sheet.set_column(col, col + 1, 3)
                            result_sheet.merge_range(row, col, row, col + 1, sub, cell_center)
                            col += 2
                    else:
                        result_sheet.set_column(col, col, 4)
                        result_sheet.write_string(row, col, sub, cell_center)
                        col += 1

                term_tot = '%s Total' % term
                result_sheet.merge_range(row - 1, col, row - 1, col + 3, term_tot, cell_center)
                for tc in term_comp:
                    result_sheet.set_column(col, col, 4)
                    result_sheet.write_string(row, col, tc, cell_center)
                    col += 1

            row -= 1
            comp_row = row + 1
            both_term_start_col = col
            both_term_tot_marks = total_marks * 2
            if the_class.standard in ninth_tenth:
                both_term_tot_marks = total_marks
            print('both_term_tot_marks = %i' % both_term_tot_marks)
            both_term_tot = 'Both Term Total (%s)' % str(both_term_tot_marks)
            if the_class.standard in ninth_tenth:
                both_term_tot = 'Academic Year Total (%s)' % str(both_term_tot_marks)
            result_sheet.merge_range(row, col, row, col + 3, both_term_tot, cell_center)
            for tc in term_comp:
                result_sheet.write_string(comp_row, col, tc, cell_center)
                result_sheet.set_column(col, col, 4)
                col += 1

            co_schol = ['Work Ed', 'Art/Music', 'Health/Phy Act', 'Discipline']
            for co in co_schol:
                result_sheet.merge_range(row, col, row + 1, col, co, vertical_text)
                result_sheet.set_column(col, col, 3)
                col += 1

            result_sheet.set_column(col, col, 25)
            result_sheet.merge_range(row, col, row + 1, col, 'Class Teacher\nRemarks', cell_center)
            col += 1

            result_sheet.set_column(col, col, 8)
            result_sheet.merge_range(row, col, row + 1, col, 'Result', cell_center)
            col += 1
            result_sheet.merge_range(row, col, row + 1, col, 'Result Remarks', cell_center)

            # header rows are ready, now is the time to get the result of each student
            row += 2
            start_row = row  # 17/10/2018 - will be used for determining rank

            last_col = col + 1
            try:
                students = Student.objects.filter(school=school, current_class=the_class,
                                                  current_section=section,
                                                  active_status=True).order_by('fist_name')
                stud_count = students.count()
                print('total %i students in class %s %s' % (stud_count, the_class.standard, section.section))
                print ('retrieved the list of students for %s-%s' % (the_class.standard, section.section))
                print (students)
                # prepare the borders
                for a_row in range(row, students.count() * 6 + row):
                    for col in range(0, last_col):
                        result_sheet.write(a_row, col, '', border)
            except Exception as e:
                print ('exception 20012018-A from exam views.py %s %s' % (e.message, type(e)))
                print ('failed to retrieve the list of students for %s-%s' %
                       (the_class.standard, section.section))
            s_no = 1
            col = 0

            for student in students:
                # result_sheet.merge_range(row, col, row + 5, col, s_no, cell_normal)
                result_sheet.merge_range(row, col, row + 6, col, s_no, cell_normal)
                col += 1
                admission_no = student.student_erp_id

                student_name = '%s %s' % (student.fist_name, student.last_name)

                # get the house information
                house = ' '
                try:
                    h = House.objects.get(student=student)
                    house = h.house
                except Exception as e:
                    print('exception 28032018-A from exam views.py %s %s' % (e.message, type(e)))
                    print('failed to retrieve house for %s' % student_name)
                # result_sheet.merge_range(row, col, row + 5, col, house, cell_normal)
                result_sheet.merge_range(row, col, row + 6, col, house, cell_normal)
                col += 1

                # result_sheet.merge_range(row, col, row + 5, col,
                #                          ('%s\n(%s)' % (student_name, admission_no)), cell_normal)
                result_sheet.merge_range(row, col, row + 6, col,
                                         ('%s\n(%s)' % (student_name, admission_no)), cell_normal)
                col += 1

                # todo insert the code for getting the third language here
                third_lang = ' '
                try:
                    tl = ThirdLang.objects.get(student=student)
                    third_lang = tl.third_lang.subject_name
                    print('retrieve the third language % s for %s of %s-%s' %
                          (third_lang, student_name, the_class.standard, section.section))
                except Exception as e:
                    print('exception 19102018-B from exam views.py %s %s' % (e.message, type(e)))
                    print('failed to retrieve the third language for %s %s of %s-%s' %
                          (student.fist_name, student.last_name, the_class.standard, section.section))
                pa = 'PA'
                ma = 'MA'  # 26/09/2019 - Multiple Assessment new Component
                nb = 'PF'  # 26/09/2019 - earlier it was Notebook Submission now Portfolio
                se = 'SE'
                the_term = 'Term'
                tot = 'Tot'
                gr = 'Gr'

                comp_title_created = False

                if the_class.standard in middle_classes:
                    print('%s is in middle_classes' % the_class.standard)
                    wing = middle_classes
                if the_class.standard in ninth_tenth:
                    print('%s is in ninth_tenth' % the_class.standard)
                    wing = ninth_tenth
                if the_class.standard in higher_classes:
                    print('%s is in higher_classes' % the_class.standard)
                    wing = higher_classes
                start_class = wing[0]
                print('start class would be %s' % start_class)
                end_class = wing[len(wing) - 1]
                print('end class would be %s' % end_class)
                term_exams = Exam.objects.filter(school=school, exam_type='term',
                                                 start_class=start_class, end_class=end_class)
                print('term exam count = %i' % term_exams.count())
                print('term exams: %s' % term_exams)
                both_term_tot_formula = '=sum('

                for index, term in enumerate(term_exams):
                    if term_exams.count() > 1:
                        if the_class.standard in ninth_tenth and index == 0:
                            continue
                    # we will be using formulas to calculate total
                    term_total_formula = '=sum('
                    rank_range = '('

                    for s in sub_list:
                        if s == 'GK':
                            try:
                                result_sheet.set_column(col, col, 3)
                                gk = Subject.objects.get(school=school, subject_name=s)
                                gk_tests = ClassTest.objects.filter(the_class=the_class,
                                                                    section=section, subject=gk)
                                gk_grade = ' '
                                if index == 0:
                                    tr1 = TestResults.objects.get(class_test=gk_tests.first(), student=student)
                                    gk_grade1 = tr1.grade
                                    gk_grade = gk_grade1
                                    print('GK grade secured by %s %s of %s-%s in %s: %s' %
                                          (student.fist_name, student.last_name, the_class.standard,
                                           section.section, term, gk_grade))
                                gk_grade2 = ' '
                                if index == 1:
                                    tr2 = TestResults.objects.get(class_test=gk_tests.last(), student=student)
                                    gk_grade2 = '%s' % tr2.grade
                                    print('GK grade secured by %s %s of %s-%s in %s: %s' %
                                          (student.fist_name, student.last_name, the_class.standard,
                                           section.section, term, gk_grade))
                                    gk_grade = gk_grade2
                                # gk_grade = '%s%s' % (gk_grade1, gk_grade2)

                                print('GK grade secured by %s: %s' % (student_name, gk_grade))
                            except Exception as e:
                                print('exception 22032018-A from exam views.py %s %s' % (e.message, type(e)))
                                print('could not retrieve the GK grade for %s' % student_name)
                                gk_grade = 'TBE '

                            # result_sheet.merge_range(row, col, row + 5, col, gk_grade, cell_grade)
                            result_sheet.merge_range(row, col, row + 6, col, gk_grade, cell_grade)
                            col += 1
                        else:
                            try:
                                if s == 'Third Language':
                                    result_sheet.set_column(col, col, 3)
                                    result_sheet.set_column(col + 1, col + 2, 4.5)  # those were extra wide.
                                    # result_sheet.merge_range(row, col, row + 5, col, third_lang, vertical_text)
                                    result_sheet.merge_range(row, col, row + 6, col, third_lang, vertical_text)
                                    col += 1
                                    subject = tl.third_lang
                                else:
                                    subject = Subject.objects.get(school=school, subject_name=s)
                                print ('retrieved the subject object for %s' % s)
                                print (subject)
                                try:
                                    term_test = ClassTest.objects.get(the_class=the_class, section=section,
                                                                      subject=subject, exam=term)
                                    print ('retrieved the term tests for class: %s-%s, subject: %s' %
                                           (the_class.standard, section.section, s))
                                    print (term_test)
                                except Exception as e:
                                    print('failed to retrieve term_test for %s class %s exam %s' %
                                          (subject.subject_name, the_class.standard, term.title))
                                    print('exception 22012019-A from exam views.py %s %s' % (e.message, type(e)))
                                    # result_sheet.merge_range(row, col, row + 5, col + 1, 'TBE', cell_center)
                                    result_sheet.merge_range(row, col, row + 6, col + 1, 'TBE', cell_center)
                                    col += 2
                                    continue
                            except Exception as e:
                                print ('exception 20012018-B from exam views.py %s %s' % (e.message, type(e)))
                                print ('failed to retrieve subject for %s' % s)
                                if subject.subject_name != 'GK':
                                    result_sheet.merge_range(row, col, row, col + 3, 'TBE', cell_grade)
                                    col += 6
                                else:
                                    result_sheet.write_string(row, col, 'TBE', cell_grade)
                                    col += 1
                                continue
                            sub_total_formula = '=sum('
                            try:
                                print ('retrieving % s marks for %s' % (s, student_name))
                                test_result = TestResults.objects.get(class_test=term_test, student=student)
                                term_marks = test_result.marks_obtained

                                # 17/10/2018 - deal with cases of marks not yet entered or Absent
                                if term_marks == -5000 or term_marks == -5000.0 or term_marks == -5000.00:
                                    print('marks not entered case')
                                    print(term_marks)
                                    print('%s test for %s for %s created but marks/absence not entered' %
                                          (subject.subject_name, term.title, student_name))
                                    result_sheet.set_column(col, col, 4)
                                    term_marks = 'TBE'

                                if term_marks == -1000 or term_marks == -1000.0 or term_marks == -1000.00:
                                    print('absence case')
                                    print(term_marks)
                                    print('%s absent (ABS) in  %s test for %s for ' %
                                          (student_name, subject.subject_name, term.title))
                                    result_sheet.set_column(col, col, 4)
                                    term_marks = 'ABS'

                                term_test_result = TermTestResult.objects.get(test_result=test_result)

                                if comp_title_created:
                                    result_sheet.set_column(col, col, 0)
                                else:
                                    comp_title_created = True

                                result_sheet.write_string(row, col, pa, cell_component)
                                col += 1
                                pa_marks = Decimal(round(term_test_result.periodic_test_marks))
                                result_sheet.write_number(row, col, pa_marks, cell_normal)
                                cell = xl_rowcol_to_cell(row, col)
                                sub_total_formula += '%s,' % (cell)
                                row += 1
                                col -= 1

                                result_sheet.write_string(row, col, ma, cell_component)
                                col += 1
                                ma_marks = Decimal(round(term_test_result.multi_asses_marks))
                                if ma_marks < 0:
                                    print('Multi Assessment marks not entered for %s in %s for %s' %
                                          (student_name, subject.subject_name, term.title))
                                    result_sheet.write_string(row, col, 'TBE', cell_grade)
                                else:
                                    result_sheet.write_number(row, col, ma_marks, cell_normal)
                                cell = xl_rowcol_to_cell(row, col)
                                sub_total_formula += '%s,' % (cell)
                                row += 1
                                col -= 1

                                result_sheet.write_string(row, col, nb, cell_component)
                                col += 1
                                nb_marks = term_test_result.note_book_marks
                                if nb_marks < 0:
                                    print('Notebook submission marks not entered for %s in %s for %s' %
                                          (student_name, subject.subject_name, term.title))
                                    result_sheet.write_string(row, col, 'TBE', cell_grade)
                                else:
                                    result_sheet.write_number(row, col, nb_marks, cell_normal)
                                cell = xl_rowcol_to_cell(row, col)
                                sub_total_formula += '%s,' % (cell)
                                row += 1
                                col -= 1

                                result_sheet.write_string(row, col, se, cell_component)
                                col += 1
                                se_marks = term_test_result.sub_enrich_marks
                                if se_marks < 0:
                                    print('Subject Enrichment submission marks not entered for %s in %s for %s' %
                                          (student_name, subject.subject_name, term.title))
                                    result_sheet.write_string(row, col, 'TBE', cell_grade)
                                else:
                                    result_sheet.write_number(row, col, se_marks, cell_normal)
                                cell = xl_rowcol_to_cell(row, col)
                                sub_total_formula += '%s,' % (cell)
                                row += 1
                                col -= 1

                                result_sheet.write_string(row, col, the_term, cell_component)
                                col += 1
                                if term_marks == 'ABS' or term_marks == 'TBE':
                                    result_sheet.write_string(row, col, term_marks, cell_grade)
                                else:
                                    result_sheet.write_number(row, col, term_marks, cell_normal)
                                cell = xl_rowcol_to_cell(row, col)
                                sub_total_formula += '%s)' % (cell)
                                row += 1
                                col -= 1

                                result_sheet.write_string(row, col, tot, cell_component)
                                col += 1
                                print('formula constructed = %s' % sub_total_formula)
                                result_sheet.write_formula(row, col, sub_total_formula, cell_bold)
                                # the above cell, in which we are writing the subject total, is a component
                                # for calculating the term total
                                cell = xl_rowcol_to_cell(row, col)
                                term_total_formula += '%s,' % (cell)
                                both_term_tot_formula += '%s,' % (cell)

                                row += 1
                                col -= 1

                                grade_formula = '=IF(%s > 90, "A1", IF(%s > 80, "A2", IF(%s > 70, "B1", ' \
                                                'IF(%s > 60, "B2", ' \
                                                'IF(%s > 50, "C1", IF(%s > 40, "C2", IF(%s > 32, "D", "E")))))))' % \
                                                (cell, cell, cell, cell, cell, cell, cell)
                                result_sheet.write_string(row, col, gr, cell_component)
                                col += 1
                                result_sheet.write_formula(row, col, grade_formula, cell_bold)

                                # 19/10/2018 - for the next subject, row and columns need to be reset
                                # row -= 5
                                row -= 6
                                col += 1
                            except Exception as e:
                                print ('exception 20012018-D from exam views.py %s %s' % (e.message, type(e)))
                                print ('failed to retrieve %s marks for %s' % (s, student_name))
                    term_total_formula += ')'
                    print('term_total_formula = %s' % term_total_formula)
                    result_sheet.set_column(col, col, 4)
                    # result_sheet.merge_range(row, col, row + 5, col, term_total_formula, cell_grade)
                    result_sheet.merge_range(row, col, row + 6, col, term_total_formula, cell_grade)
                    result_sheet.write_formula(row, col, term_total_formula, cell_grade)
                    cell = xl_rowcol_to_cell(row, col)
                    rank_range += '%s,' % cell
                    col += 1

                    perc_formula = '=%s/%s' % (cell, str(total_marks))
                    # result_sheet.merge_range(row, col, row + 5, col, perc_formula, cell_grade)
                    result_sheet.merge_range(row, col, row + 6, col, perc_formula, cell_grade)
                    result_sheet.write_formula(row, col, perc_formula, perc_format)
                    result_sheet.set_column(col, col, 6)
                    cell = xl_rowcol_to_cell(row, col, row_abs=True, col_abs=True)
                    col += 1

                    grade_formula = '=IF(%s*100 > 90, "A1", IF(%s*100 > 80, "A2", IF(%s*100 > 70, "B1", ' \
                                    'IF(%s*100 > 60, "B2", ' \
                                    'IF(%s*100 > 50, "C1", IF(%s*100 > 40, "C2", IF(%s*100 > 32, "D", "E")))))))' % \
                                    (cell, cell, cell, cell, cell, cell, cell)
                    # result_sheet.merge_range(row, col, row + 5, col, grade_formula, cell_grade)
                    result_sheet.merge_range(row, col, row + 6, col, grade_formula, cell_grade)
                    result_sheet.write_formula(row, col, grade_formula, cell_grade)
                    col += 1

                    # determine the rank
                    cell = xl_rowcol_to_cell(row, col - 2)
                    cell_start = xl_rowcol_to_cell(start_row, col - 2, row_abs=True, col_abs=True)
                    cell_end = xl_rowcol_to_cell(start_row + stud_count * 7 - 1, col - 2, row_abs=True,
                                                 col_abs=True)
                    rank_formula = '=RANK(%s, %s:%s)' % (cell, cell_start, cell_end)
                    print('formula for rank: %s', rank_formula)
                    # result_sheet.merge_range(row, col, row + 5, col, rank_formula, cell_grade)
                    result_sheet.merge_range(row, col, row + 6, col, rank_formula, cell_grade)
                    result_sheet.write_formula(row, col, rank_formula, cell_grade)
                    col += 1
                both_term_tot_formula += ')'
                print('both_term_total_formula = %s' % both_term_tot_formula)

                # 20/10/2018 - summary for both terms
                col = both_term_start_col
                # result_sheet.merge_range(row, col, row + 5, col, both_term_tot_formula, cell_grade)
                result_sheet.merge_range(row, col, row + 6, col, both_term_tot_formula, cell_grade)
                result_sheet.write_formula(row, col, both_term_tot_formula, cell_grade)
                cell = xl_rowcol_to_cell(row, col)
                col += 1

                perc_formula = '=%s/%s' % (cell, str(total_marks * 2))
                if the_class.standard in ninth_tenth:
                    perc_formula = '=%s/%s' % (cell, str(total_marks))
                # result_sheet.merge_range(row, col, row + 5, col, perc_formula, cell_grade)
                result_sheet.merge_range(row, col, row + 6, col, perc_formula, cell_grade)
                result_sheet.write_formula(row, col, perc_formula, perc_format)
                col += 1

                # result_sheet.merge_range(row, col, row + 5, col, grade_formula, cell_grade)
                result_sheet.merge_range(row, col, row + 6, col, grade_formula, cell_grade)
                result_sheet.write_formula(row, col, grade_formula, cell_grade)
                col += 1

                cell = xl_rowcol_to_cell(row, col - 2)
                cell_start = xl_rowcol_to_cell(start_row, col - 2, row_abs=True, col_abs=True)
                cell_end = xl_rowcol_to_cell(start_row + stud_count * 6 - 1, col - 2, row_abs=True, col_abs=True)
                rank_formula = '=RANK(%s, %s:%s)' % (cell, cell_start, cell_end)
                print('formula for rank: %s', rank_formula)
                # result_sheet.merge_range(row, col, row + 5, col, rank_formula, cell_grade)
                result_sheet.merge_range(row, col, row + 6, col, rank_formula, cell_grade)
                result_sheet.write_formula(row, col, rank_formula, cell_grade)
                col += 1

                # co-scholastic grades. We will show grades for both terms separated by /, eg B/A
                try:
                    cs_term1 = CoScholastics.objects.get(term='term1', student=student)
                    cs_term2 = CoScholastics.objects.get(term='term2', student=student)
                    work_ed1 = cs_term1.work_education
                    work_ed2 = '%s/%s' % (work_ed1, cs_term2.work_education)
                    # result_sheet.merge_range(row, col, row + 5, col,  work_ed2, cell_grade)
                    result_sheet.merge_range(row, col, row + 6, col, work_ed2, cell_grade)
                    col += 1

                    art_ed1 = cs_term1.art_education
                    art_ed2 = '%s/%s' % (art_ed1, cs_term2.art_education)
                    # result_sheet.merge_range(row, col, row + 5, col, art_ed2, cell_grade)
                    result_sheet.merge_range(row, col, row + 6, col, art_ed2, cell_grade)
                    col += 1

                    health_ed1 = cs_term1.health_education
                    health_ed2 = '%s/%s' % (health_ed1, cs_term2.health_education)
                    # result_sheet.merge_range(row, col, row + 5, col, health_ed2, cell_grade)
                    result_sheet.merge_range(row, col, row + 6, col, health_ed2, cell_grade)
                    col += 1

                    discipline1 = cs_term1.discipline
                    discipline2 = '%s/%s' % (discipline1, cs_term2.discipline)
                    # result_sheet.merge_range(row, col, row + 5, col, discipline2, cell_grade)
                    result_sheet.merge_range(row, col, row + 6, col, discipline2, cell_grade)
                    col += 1

                    teacher_remarks = cs_term2.teacher_remarks
                    print('class teacher remarks for %s of %s-%s in %s: %s' %
                          (student_name, the_class.standard, section.section, term, teacher_remarks))
                    result_sheet.set_column(col, col, 10)
                    # result_sheet.merge_range(row, col, row + 5, col, teacher_remarks, cell_normal)
                    result_sheet.merge_range(row, col, row + 6, col, teacher_remarks, cell_normal)

                    col += 1
                    try:
                        not_promoted = NPromoted.objects.get(student=student)
                        details = not_promoted.details
                        print('student %s %s has failed in class %s.' % (student.fist_name,
                                                                         student.last_name, the_class))
                        print(not_promoted)
                        promoted_status = 'Not Promoted'

                        # 14/03/2019 - we want to highlight the row of detained students. But xlxswriter
                        # only allows to highlight a cell. If we are in this block of code, means that the =
                        # student is Not Promoted. So, we chose to highlight all the cells in this row based on
                        # criteria tha the cell is not blank which is true for every cell and hence the whole
                        # row gets highlighted
                        # result_sheet.conditional_format(row, 0, row + 5, col + 1, {'type': 'no_blanks',
                        #                                                        'format': fail_format})
                        result_sheet.conditional_format(row, 0, row + 6, col + 1, {'type': 'no_blanks',
                                                                                   'format': fail_format})
                    except Exception as e:
                        print('student %s %s has passed in class %s.' % (student.fist_name, student.last_name,
                                                                         the_class))
                        print('exception 14032019-A from exam views.py %s %s' % (e.message, type(e)))
                        promoted_status = 'Promoted'
                        details = ' '
                    # result_sheet.merge_range(row, col, row + 5, col, promoted_status, cell_normal)
                    result_sheet.merge_range(row, col, row + 6, col, promoted_status, cell_normal)
                    col += 1
                    # result_sheet.merge_range(row, col, row + 5, col, details, cell_normal)
                    result_sheet.merge_range(row, col, row + 6, col, details, cell_normal)

                except Exception as e:
                    print ('exception 21012018-A from exam views.py %s %s' % (e.message, type(e)))
                    print ('failed to retrieve Co-scholastics grade for %s' % student_name)

                col = 0
                # row += 6
                row += 7
                s_no = s_no + 1
        if the_class.standard in ninth_tenth:
            print('hiding columns for class IX')
            for col in range(16, 37):
                result_sheet.set_column(col, col, options={'hidden': True})

        if the_class.standard in higher_classes:
            maths_stream = ['English', 'Mathematics', 'Physics', 'Chemistry', 'Elective']
            bio_stream = ['English', 'Biology', 'Physics', 'Chemistry', 'Elective']
            commerce_stream = ['English', 'Economics', 'Accountancy', 'Business Studies', 'Elective']
            humanities_stream = ['English', 'Economics', 'History', 'Sociology', 'Elective']
            components = ['UT', 'Half Yearly', 'Final Exam', 'Cumulative']
            try:
                students = Student.objects.filter(school=school, current_class=the_class, current_section=section,
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
                        if 'Accountancy' in sub_dict:
                            chosen_stream = commerce_stream
                            print('%s %s has chosen %s stream' %
                                  (the_class.standard, section.section, 'commerce'))
                        if 'History' in sub_dict:
                            chosen_stream = humanities_stream
                            print('%s %s has chosen %s stream' %
                                  (the_class.standard, section.section, 'humanities'))
                    except Exception as e:
                        print('failed to determine the stream chosen by %s %s' %
                              (student.fist_name, student.last_name))
                        print('exception 03032018-A from exam views.py %s %s' % (e.message, type(e)))
                    row = 3
                    col = 3
                    result_sheet.merge_range(row, col, row + 2, col, 'Elective Sub', vertical_text)
                    col = col + 1
                    result_sheet.set_column('D:D', 6)
                    result_sheet.set_column('E:BH', 4.5)
                    for sub in chosen_stream:
                        print('now creating heading for subject: %s' % sub)
                        result_sheet.merge_range(row, col, row, col + 10, sub, cell_center)
                        col1 = col

                        # UT
                        result_sheet.merge_range(row + 1, col1, row + 2, col1, components[0], cell_center)
                        col1 = col1 + 1

                        # Half Yearly Exam
                        result_sheet.merge_range(row + 1, col1, row + 1, col1 + 2, components[1], cell_center)
                        result_sheet.write_string(row + 2, col1, 'Th', cell_center)
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
                result_sheet.set_column('BI:BI', 4.5)
                result_sheet.set_column('BJ:BO', 2.5)
                g_col = 59
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'Grand Total', vertical_text)
                g_col += 1
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'Percentage', vertical_text)
                g_col += 1
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'Grade', vertical_text)
                g_col += 1
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'Rank', vertical_text)
                g_col += 1
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'GS', vertical_text)
                g_col += 1
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'Work Ex', vertical_text)
                g_col += 1
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'PHED', vertical_text)
                g_col += 1
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'Discipline', vertical_text)
                g_col += 1
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'Result', cell_center)
                g_col += 1
                result_sheet.merge_range(row, g_col, row + 2, g_col, 'Details', cell_center)
                row += 3

                # delete the "Elective" entry from the sub_dict. We will now substitute it with the real
                # elective chosen by each student.
                chosen_stream.pop()

                ut_list = Exam.objects.filter(school=school, exam_type='unit', start_class='XI')
                s_no = 1
                for student in students:
                    col = 0
                    result_sheet.write_number(row, col, s_no, cell_normal)
                    col += 1
                    admission_no = student.student_erp_id
                    student_name = student.fist_name + ' ' + student.last_name
                    # get the house information
                    try:
                        h = House.objects.get(student=student)
                        house = h.house
                        result_sheet.write_string(row, col, house, cell_normal)
                    except Exception as e:
                        print('exception 28032018-A from exam views.py %s %s' % (e.message, type(e)))
                        print('failed to retrieve house for %s' % student_name)
                        result_sheet.write_string(row, col, ' ', cell_normal)
                    col += 1
                    student_name = '%s %s\n%s' % (student.fist_name, student.last_name, admission_no)
                    result_sheet.write_string(row, col, student_name, cell_normal)
                    col += 1

                    sub_dict = []
                    mapping = HigherClassMapping.objects.filter(student=student)
                    print('mapping for %s is %s' % (student_name, mapping))
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
                        ut_count = 0.0
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
                                                                 section=section, exam=a_ut)
                                    print('test was conducted for %s under exam: %s for class %s' %
                                          (sub, ut, the_class.standard))
                                    print(test)
                                    ut_count += 1.0
                                    print('ut_count = %f' % float(ut_count))
                                    result = TestResults.objects.get(class_test=test, student=student)
                                    print(result)
                                    # convert the marks to be out of 25
                                    if float(result.marks_obtained > -1000.0):
                                        comments += '%s/%s' % (str(result.marks_obtained),
                                                               str(round(test.max_marks, 0)))
                                        print(comments)
                                        # marks = (25.0*float(result.marks_obtained))/(float(test.max_marks))
                                        marks = float(result.marks_obtained)
                                        ut_total += marks
                                        print('ut_total = %f' % ut_total)
                                except Exception as e:
                                    print('no test could be found corresponding to %s class %s subject %s' %
                                          (ut, the_class.standard, sub))
                                    print('exception 04032018-B from exam views.py %s %s'
                                          % (e.message, type(e)))
                            except Exception as e:
                                print('%s could not be retrieved for class %s' % (ut, the_class.standard))
                                print('exception 04032018-C from exam views.py %s %s' % (e.message, type(e)))
                                col += 1
                        try:
                            result_sheet.write_number(row, col, round(ut_total / float(ut_count), 2), cell_normal)
                            result_sheet.write_comment(row, col, comments, {'height': 150})
                        except Exception as e:
                            print('UT average not available for %s in %s' %
                                  (student_name, subject.subject_name))
                            print('exception 30012019-A from exam views.py %s %s' % (e.message, type(e)))
                        col += 1

                        # get the half yearly marks & final exam marks
                        term_exams = Exam.objects.filter(school=school, exam_type='term',
                                                         start_class='XI')
                        prac_subjects = ["Biology", "Physics", "Chemistry", "Fine Arts",
                                         "Accountancy", "Business Studies", "Economics",
                                         "Information Practices", "Informatics Practices", "Computer Science",
                                         "Painting",
                                         "Physical Education"]
                        for term in term_exams:
                            try:
                                test = ClassTest.objects.get(subject=subject, the_class=the_class,
                                                             section=section, exam=term)
                                print('test was conducted for %s under exam: %s for class %s' %
                                      (sub, term, the_class.standard))
                                print(test)
                                result = TestResults.objects.get(class_test=test, student=student)
                                print(result)
                                if result.marks_obtained > -1000.0:
                                    result_sheet.write_number(row, col,
                                                              float(result.marks_obtained), cell_normal)
                                else:
                                    if result.marks_obtained == -1000.0 or result.marks_obtained == -1000.00:
                                        result_sheet.write_string(row, col, 'ABS', cell_center)
                                    if result.marks_obtained == -5000.0 or result.marks_obtained == -5000.00:
                                        result_sheet.write_string(row, col, 'TBE', cell_center)

                                col += 1

                                if subject.subject_prac:
                                    # if sub in prac_subjects:
                                    try:
                                        term_test_results = TermTestResult.objects.get(test_result=result)
                                        print('%s has practical component' % (sub))
                                        prac_marks = float(term_test_results.prac_marks)

                                        if prac_marks > -1000.00:
                                            result_sheet.write_number(row, col, prac_marks, cell_normal)
                                        else:
                                            if prac_marks == -1000.0 or prac_marks == -1000.00:
                                                result_sheet.write_string(row, col, 'ABS', cell_center)
                                            if prac_marks == -5000.0 or prac_marks == -5000.00:
                                                result_sheet.write_string(row, col, 'TBE', cell_center)

                                        col += 1
                                        result_sheet.set_column(col + 1, col + 7, options={'hidden': True})

                                    except Exception as e:
                                        print('%s practical marks for %s could not be retrieved' %
                                              (sub, student_name))
                                        print('exception 04032018-D from exam views.py %s %s' %
                                              (e.message, type(e)))
                                        col += 1
                                else:
                                    result_sheet.write_string(row, col, 'NA', cell_normal)
                                    col += 1
                                # 20/02/2019 for cumulative only theory marks are to be taken into
                                # account for Half yearly and Annual Exams
                                # cell_range = xl_range(row, col-2, row, col-2)
                                # formula = '=SUM(%s)' % cell_range
                                # result_sheet.write_formula(row, col, formula, cell_normal)
                                col += 1
                            except Exception as e:
                                print('no test could be found corresponding to %s class %s subject %s' %
                                      (ut, the_class.standard, sub))
                                print('exception 04032018-B from exam views.py %s %s'
                                      % (e.message, type(e)))
                                col += 3
                                # col += 5
                        # fill in cumulative results
                        # get the UT cell
                        cell = xl_rowcol_to_cell(row, col - 7)
                        formula = '=%s' % cell
                        result_sheet.write_formula(row, col, formula, cell_normal)
                        # col += 1
                        col += 4

                        commerce_sub = ['Economics', 'Accountancy', 'Business Studies']
                        # get the half yearly total cell
                        cell = xl_rowcol_to_cell(row, col - 5)
                        # if subject.subject_prac:
                        if subject.subject_name not in commerce_sub:
                            formula = '=%s * 25/%f' % (cell, subject.theory_marks)
                        else:
                            formula = '=%s * 25/%f' % (cell, 100.00)
                        # else:
                        #     formula = '=%s/4.0' % cell
                        result_sheet.write_formula(row, col, formula, cell_normal)
                        col += 1

                        # get the final exam total cell
                        cell = xl_rowcol_to_cell(row, col - 3)
                        formula = '=%s * 50/%f' % (cell, subject.theory_marks)
                        result_sheet.write_formula(row, col, formula, cell_normal)
                        col += 1

                        # write the grand total
                        cell_range = xl_range(row, col - 3, row, col - 1)
                        formula = '=SUM(%s)' % cell_range
                        result_sheet.write_formula(row, col, formula, cell_normal)
                        col += 1

                    # write the total for all subjects for this student
                    c1 = xl_rowcol_to_cell(row, 14)
                    c2 = xl_rowcol_to_cell(row, 25)
                    c3 = xl_rowcol_to_cell(row, 36)
                    c4 = xl_rowcol_to_cell(row, 47)
                    c5 = xl_rowcol_to_cell(row, 58)
                    formula = '=ROUND(SUM(%s, %s, %s, %s, %s), 1)' % (c1, c2, c3, c4, c5)
                    print('formula for grand total = %s' % formula)
                    result_sheet.write_formula(row, col, formula, cell_normal)
                    col += 1

                    # percentage
                    cell_range = xl_range(row, col - 1, row, col - 1)
                    formula = '=%s/500.00' % cell_range
                    result_sheet.write_formula(row, col, formula, perc_format)
                    col += 1

                    index = 'BI%s*100' % str(row + 1)
                    print ('index = %s' % index)
                    formula = '=IF(%s > 90, "A1", IF(%s > 80, "A2", IF(%s > 70, "B1", IF(%s > 60, "B2", ' \
                              'IF(%s > 50, "C1", IF(%s > 40, "C2", IF(%s > 32, "D", "E")))))))' % \
                              (index, index, index, index, index, index, index)
                    print ('formula for grade = %s' % formula)
                    result_sheet.write_formula(row, col, formula, cell_grade)

                    col += 1
                    # determine the rank
                    count = students.count()
                    start_row = 7
                    formula = '=RANK(BI%s, $BI$%s:$BI$%s)' % (str(row + 1), str(start_row), str(count + 7))
                    print('formula for rank: %s', formula)
                    result_sheet.write_formula(row, col, formula, cell_grade)
                    col += 1

                    try:
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
                    except Exception as e:
                        print('failed to retrieve co-scholastic for %s' % student_name)
                        print('exception 29012019-A from exam views.py %s %s' % (e.message, type(e)))
                        col += 4

                    # show the result/remarks. In the beginning it will show Promoted,
                    #  but after the analysis is done, it will show the actual result
                    print('now determining the promoted status for %s' % student)
                    result_sheet.set_column('BQ:BQ', 15)
                    result_sheet.set_column('BR:BR', 30)
                    details = ' '
                    try:
                        not_promoted = NPromoted.objects.get(student=student)
                        details = not_promoted.details
                        print('student %s %s has failed in class %s.' % (student.fist_name,
                                                                         student.last_name, the_class))
                        print(not_promoted)
                        promoted_status = 'Not Promoted'

                        # 14/03/2019 - we want to highlight the row of detained students. But xlxswriter
                        # only allows to highlight a cell. If we are in this block of code, means that the =
                        # student is Not Promoted. So, we chose to highlight all the cells in this row based on
                        # criteria tha the cell is not blank which is true for every cell and hence the whole
                        # row gets highlighted
                        result_sheet.conditional_format(row, 0, row, col + 1, {'type': 'no_blanks',
                                                                               'format': fail_format})
                    except Exception as e:
                        print('student %s %s has passed in class %s.' % (student.fist_name, student.last_name,
                                                                         the_class))
                        print('exception 25032018-C from exam views.py %s %s' % (e.message, type(e)))
                        promoted_status = 'Promoted'
                    result_sheet.write_string(row, col, promoted_status, cell_normal)

                    col += 1
                    result_sheet.write_string(row, col, details, cell_normal)
                    # reset the chosen_stream to standard subjects
                    chosen_stream.pop()
                    row += 1
                    s_no += 1
            except Exception as e:
                print('failed to retrieve the list of students for class %s-%s' %
                      (the_class.standard, section.section))
                print('exception 03032018-B from exam views.py %s %s' % (e.message, type(e)))
        row += 4
        sig_col = 3
        result_sheet.merge_range(row, sig_col, row, sig_col + 6, "Class Teacher's Signature", title)
        sig_col += 10
        result_sheet.merge_range(row, sig_col, row, sig_col + 6, "Vice Principal's Signature", title)
        sig_col += 10
        result_sheet.merge_range(row, sig_col, row, sig_col + 6, "Principal's Signature", title)
        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response
