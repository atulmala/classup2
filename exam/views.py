from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import xlrd

from setup.forms import ExcelFileUploadForm
from setup.models import School
from setup.views import validate_excel_extension

from student.models import Student, DOB
from academics.models import Class, Section, Subject, ThirdLang, ClassTest, \
    Exam, TermTestResult, TestResults, CoScholastics

from .models import Scheme, HigherClassMapping
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
    context_dict = {}
    context_dict['user_type'] = 'school_admin'
    context_dict['school_name'] = request.session['school_name']

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
                                erp = s.student_erp_id[:-3]
                                print ('erp = %s' % erp)
                                if erp == partial_erp:
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
    if marks <= 90 and marks > 80:
        grade = 'A2'
        return grade
    if marks <= 80 and marks > 70:
        grade = 'B1'
        return grade
    if marks <= 70 and marks > 60:
        grade = 'B2'
        return grade
    if marks <= 60 and marks > 50:
        grade = 'C1'
        return grade
    if marks <= 50 and marks > 40:
        grade = 'C2'
        return grade
    if marks <= 40 and marks > 32:
        grade = 'D'
        return grade
    if marks <= 32:
        grade = 'E (Needs Improvement)'
        return grade


# we need to exempt this view from csrf verification. Will be updated in next version when
# we will implement authentication


@csrf_exempt
def prepare_results(request, school_id, the_class, section):
    school = School.objects.get(id=school_id)
    school_name = school.school_name
    print(school)
    standard = Class.objects.get(school=school, standard=the_class)
    print(standard)
    sec = Section.objects.get(school=school, section=section)
    print(sec)

    if request.method == 'GET':
        print(request.body)
        whole_class = request.GET.get('whole_class')
        print(whole_class)
        selected_student = request.GET.get('selected_student')
        print (selected_student)

        # 02/11/2017 - get the scheme for this class. The scheme will provide the subjects of this class and
        # the sequence. Subjects in the Marksheet would appear in the order of sequence
        sub_dict = {}
        scheme = Scheme.objects.filter(school=school, the_class=standard)
        sub_count = scheme.count()
        for s in scheme:
            sub_dict[s.sequence] = s.subject
        print (sub_dict)

        # 20/10/2017 - now the grand loop starts!

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
        table1_top = stu_detail_top - 275
        tab = 80

        c.setFont(font, 14)

        style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                  ('BOX', (0, 0), (-1, -1), 2, colors.black),
                  ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                  ('ALIGN', (1, 0), (6, 0), 'CENTER'),
                  ('SPAN', (1, 0), (6, 0)),
                  ('FONTSIZE', (0, 0), (-1, -1), 8),
                  ('FONT', (0, 0), (6, 0), 'Times-Bold'),
                  ('FONT', (0, 1), (0, 1), 'Times-Bold')
                  ]
        style2 = style3 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                            ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                                            ('SPAN', (0, 0), (1, 0)),
                                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                                            ('FONT', (0, 0), (1, 0), 'Times-Bold')
                                            ]
        style4 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                            ('FONT', (0, 0), (1, 0), 'Times-Bold'),
                                            ('FONTSIZE', (0, 0), (-1, -1), 8)]
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
        father_name_lbl = 'Father Name:'
        dob_lbl = 'Date of Birth:'
        class_sec_lbl = 'Class/Section:'

        exam = Exam.objects.get(school=school, title='Term1')
        print(exam)
        start_date = exam.start_date
        end_date = exam.end_date

        if whole_class == 'true':
            # get the list of all the students, then get the marks of each test conducted for this exam
            students = Student.objects.filter(school=school, current_class=standard, current_section=sec)
            for s in students:
                print('Entering loop')
                c.translate(inch, inch)
                c.drawString(141, top, school_name)
                c.line(0, line_top, 6 * inch, line_top)

                c.setFont(font, 10)
                c.drawString(152, session_top, session)
                print('heading created')

                report_card = 'Report Card for Class ' + the_class + '-' + section
                c.drawString(152, report_card_top, report_card)

                c.setFont(font, 10)

                c.drawString(0, stu_detail_top, adm_no_lbl)
                c.drawString(tab, stu_detail_top, s.student_erp_id)

                c.drawString(0, stu_detail_top - 15, stu_name_lbl)
                c.drawString(tab, stu_detail_top - 15, s.fist_name + ' ' + s.last_name)

                c.drawString(0, stu_detail_top - 30, father_name_lbl)
                c.drawString(tab, stu_detail_top - 30, s.parent.parent_name)

                c.drawString(0, stu_detail_top - 45, dob_lbl)
                try:
                    d = DOB.objects.get(student=s)
                    dob = d.dob
                    print(dob)
                    c.drawString(tab, stu_detail_top - 45, dob.strftime('%d-%m-%Y'))
                except Exception as e:
                    print ('date of birth not yet set for %s %s ' % (s.fist_name, s.last_name))
                    print('Exception 23102017-A from exam views.py %s %s ' % (e.message, type(e)))


                c.drawString(0, stu_detail_top - 60, class_sec_lbl)
                c.drawString(tab, stu_detail_top - 60, the_class + '-' + section)
                print('report heading prepared')
                data1 = [['Scholastic\nAreas', 'Term-1 (100 Marks)', '', '', '', '', ''],
                         ['Sub Name', 'Per Test\n(10)', 'Note Book\n(5)', 'Sub\nEnrichment\n(5)',
                          'Half\nYearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade']]

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
                            print ('failed to determine third lang for %s. Exception 061117-A from exam views.py %s %s' %
                                   (s.fist_name, e.message, type(e)))
                    try:
                        test = ClassTest.objects.get(subject=sub, the_class=standard, section=sec,
                                                           date_conducted__gte=start_date, date_conducted__lte=end_date)
                        tr = TestResults.objects.get(class_test=test, student=s)

                        main = tr.marks_obtained
                        tr = TermTestResult.objects.get(test_result=tr)

                        pa = tr.periodic_test_marks

                        notebook = tr.note_book_marks

                        sub_enrich = tr.sub_enrich_marks

                        total = float(main) + float(pa) + float(notebook) + float(sub_enrich)

                        grade = get_grade(total)
                        print(grade)

                        sub_row = [sub.subject_name, pa, notebook, sub_enrich, main, total, grade]
                        data1.append(sub_row)
                        print(data1)
                    except Exception as e:
                        print('Error while preparing results')
                        print ('Exception 21102017-A from exam views.py %s %s' % (e.message, type(e)))

                try:
                    table1 = Table(data1)
                    table1.setStyle(TableStyle(style1))

                    table1.wrapOn(c, 0, 0)
                    table1.drawOn(c, 0, table1_top)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-H from exam views.py %s %s' % (e.message, type(e)))

                # get the CoScholastic Grades for this student
                co_scl = CoScholastics.objects.get(term='Term1', student=s)
                work_ed = co_scl.work_education
                art_ed = co_scl.art_education
                health_ed = co_scl.health_education
                dscpln = co_scl.discipline
                remark = co_scl.teacher_remarks

                data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale', ''],
                         ['Work Education (or Pre-vocational Education', work_ed],
                         ['Art Education', art_ed],
                         ['Health & Physical Education', health_ed]]
                table2_top = table1_top - 100
                table2 = Table(data2)
                table2.setStyle(TableStyle(style2))
                table2.wrapOn(c, 0, 0)
                table2.drawOn(c, 0, table2_top)

                data3 = [['Grade', 'Grade'],
                         ['Discipline: Term-1[On a 3-point(A-C) grading scale', dscpln]]
                table3_top = table2_top - 50
                table3 = Table(data3)
                table3.setStyle(TableStyle(style3))
                table3.wrapOn(c, 0, 0)
                table3.drawOn(c, 0, table3_top)

                c.drawString(0, table3_top - 20, 'Class Teacher Remarks: ')
                c.drawString(tab+30, table3_top - 20, remark)
                c.drawString(0, table3_top - 45, 'Place & Date:')
                c.drawString(150, table3_top - 45, 'Signature of Class Teacher')
                c.drawString(300, table3_top - 45, 'Signature of Principal')

                c.line(0, table3_top - 50, 6 * inch, table3_top - 50)
                c.drawString(170, table3_top - 60, "Instructions")
                c.drawString(0, table3_top - 70, "Grading Scale for Scholastic Areas: "
                                                 "Grades are awarded on a 8-point grading scales as follows - ")

                table4 = Table(data4)
                table4.setStyle(TableStyle(style4))
                table4.wrapOn(c, 0, 0)
                table4.drawOn(c, 120, table3_top - 250)

                c.showPage()
            try:
                c.save()
            except Exception as e:
                print('error in saving the pdf')
                print ('Exception 21102017-P from exam views.py %s %s' % (e.message, type(e)))
            print('about to send the response')
            return response

        else:
            c.translate(inch, inch)
            c.drawString(141, top, school_name)
            c.line(0, line_top, 6 * inch, line_top)

            c.setFont(font, 10)
            c.drawString(152, session_top, session)
            print('heading created')

            report_card = 'Report Card for Class ' + the_class + '-' + section
            c.drawString(152, report_card_top, report_card)

            c.setFont(font, 10)
            c.drawString(0, stu_detail_top, adm_no_lbl)
            c.drawString(tab, stu_detail_top, s.student_erp_id)

            c.drawString(0, stu_detail_top - 15, stu_name_lbl)
            c.drawString(tab, stu_detail_top - 15, s.fist_name + ' ' + s.last_name)

            c.drawString(0, stu_detail_top - 30, father_name_lbl)
            c.drawString(tab, stu_detail_top - 30, s.parent.parent_name)

            c.drawString(0, stu_detail_top - 45, dob_lbl)
            try:
                d = DOB.objects.get(student=s)
                dob = d.dob
                print(dob)
                c.drawString(tab, stu_detail_top - 45, dob.strftime('%d-%m-%Y'))
            except Exception as e:
                print ('date of birth not yet set for %s %s ' % (s.fist_name, s.last_name))
                print('Exception 23102017-A from exam views.py %s %s ' % (e.message, type(e)))

            c.drawString(0, stu_detail_top - 60, class_sec_lbl)
            c.drawString(tab, stu_detail_top - 60, the_class + '-' + section)
            print('report heading prepared')

            exam = Exam.objects.get(school=school, title='Term1')
            print(exam)
            start_date = exam.start_date
            end_date = exam.end_date

            data1 = [['Scholastic\nAreas', 'Term-1 (100 Marks)', '', '', '', '', ''],
                     ['Sub Name', 'Per Test\n(10)', 'Note Book\n(5)', 'Sub\nEnrichment\n(5)',
                      'Half\nYearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade']]
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
                        print ('failed to determine third lang for %s. Exception 061117-B from exam views.py %s %s' %
                               (s.fist_name, e.message, type(e)))
                try:
                    test = ClassTest.objects.get(subject=sub, the_class=standard, section=sec,
                                                 date_conducted__gte=start_date, date_conducted__lte=end_date)
                    tr = TestResults.objects.get(class_test=test, student=s)

                    main = tr.marks_obtained
                    tr = TermTestResult.objects.get(test_result=tr)

                    pa = tr.periodic_test_marks

                    notebook = tr.note_book_marks

                    sub_enrich = tr.sub_enrich_marks

                    total = float(main) + float(pa) + float(notebook) + float(sub_enrich)

                    grade = get_grade(total)
                    print(grade)

                    sub_row = [sub.subject_name, pa, notebook, sub_enrich, main, total, grade]
                    data1.append(sub_row)
                except Exception as e:
                    print('Error while preparing results')
                    print ('Exception 21102017-A from exam views.py %s %s' % (e.message, type(e)))

            try:
                table1 = Table(data1)
                table1.setStyle(TableStyle(style1))

                table1_top = stu_detail_top - 275
                table1.wrapOn(c, 0, 0)
                table1.drawOn(c, 0, table1_top)
            except Exception as e:
                print('Error while preparing results')
                print ('Exception 21102017-H from exam views.py %s %s' % (e.message, type(e)))

            # get the CoScholastic Grades for this student
            co_scl = CoScholastics.objects.get(term='Term1', student=s)
            work_ed = co_scl.work_education
            art_ed = co_scl.art_education
            health_ed = co_scl.health_education
            dscpln = co_scl.discipline
            remark = co_scl.teacher_remarks

            data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale', ''],
                     ['Work Education (or Pre-vocational Education', work_ed],
                     ['Art Education', art_ed],
                     ['Health & Physical Education', health_ed]]
            table2_top = table1_top - 100
            table2 = Table(data2)
            table2.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                        ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                                        ('SPAN', (0, 0), (1, 0)),
                                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                                        ('FONT', (0, 0), (1, 0), 'Times-Bold')
                                        ]))
            table2.wrapOn(c, 0, 0)
            table2.drawOn(c, 0, table2_top)

            data3 = [['Grade', 'Grade'],
                     ['Discipline: Term-1[On a 3-point(A-C) grading scale', dscpln]]
            table3_top = table2_top - 50
            table3 = Table(data3)
            table3.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                        ('BOX', (0, 0), (-1, -1), 2, colors.black),
                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                        ('ALIGN', (0, 0), (1, 0), 'RIGHT'),
                                        ('SPAN', (0, 0), (1, 0)),
                                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                                        ('FONT', (0, 0), (0, 0), 'Times-Bold')
                                        ]))
            table3.wrapOn(c, 0, 0)
            table3.drawOn(c, 0, table3_top)

            c.drawString(0, table3_top - 20, 'Class Teacher Remarks: ')
            c.drawString(tab + 30, table3_top - 20, remark)
            c.drawString(0, table3_top - 45, 'Place & Date:')
            c.drawString(150, table3_top - 45, 'Signature of Class Teacher')
            c.drawString(300, table3_top - 45, 'Signature of Principal')

            c.line(0, table3_top - 50, 6 * inch, table3_top - 50)
            c.drawString(170, table3_top - 60, "Instructions")
            c.drawString(0, table3_top - 70, "Grading Scale for Scholastic Areas: "
                                             "Grades are awarded on a 8-point grading scales as follows - ")

            data4 = [['MARKS RANGE', 'GRADE'],
                     ['91 - 100', 'A 1'],
                     ['81 - 90', 'A 2'],
                     ['71 - 80', 'B 1'],
                     ['61 - 70', 'B 2'],
                     ['51 - 60', 'C 1'],
                     ['41 - 50', 'C 2'],
                     ['33 - 40', 'D'],
                     ['32 & Below', 'E (Needs improvement)']]
            table4 = Table(data4)
            table4.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                        ('FONT', (0, 0), (1, 0), 'Times-Bold'),
                                        ('FONTSIZE', (0, 0), (-1, -1), 8)]))
            table4.wrapOn(c, 0, 0)
            table4.drawOn(c, 120, table3_top - 250)

            c.showPage()
            c.save()
            return response
    return HttpResponse()


class ResultSheet(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        school_id = request.session['school_id']
        form = ResultSheetForm(school_id=school_id)
        context_dict['form'] = form
        return render(request, 'classup/result_sheet.html', context_dict)