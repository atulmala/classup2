import StringIO

import xlrd
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from django.http import HttpResponse
from rest_framework import generics

from academics.models import Section, Class, Subject, Exam, ClassTest, TestResults, TermTestResult
from formats.formats import Formats as format

from authentication.views import JSONResponse
from setup.models import School
from student.models import Student
from exam.models import CBSERollNo


class CBSEMapping(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        print ('now starting to process the uploaded file CBSE Roll No mapping to student ERP Id...')
        fileToProcess_handle = request.FILES['JPS_CBSE_mapping.xlsx']
        print(fileToProcess_handle)

        fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
        sheet = fileToProcess.sheet_by_index(0)
        for row in range(sheet.nrows):
            # first two rows are header rows
            if row == 0:
                school_id = sheet.cell(row, 0).value
                school = School.objects.get(pk=school_id)
                print('school = %s' % school)
                continue
            print ('Processing a new row')
            try:
                erp_id = sheet.cell(row, 0).value
                decimal = '.'
                if decimal in erp_id:
                    print('student id contains a decimal followed by zero. This has to be removed')
                    erp_id = erp_id[:-2]
                    print('decimal and following zero removed. Now student_id = %s' % erp_id)
            except Exception as e:
                print('exception 31012020-A from exam cbse.py. %s %s' % (e.message, type(e)))

            try:
                student = Student.objects.get(school=school, student_erp_id=erp_id)
                print('mapping the CBSE Roll No for %s with erp_id %s' % (student, erp_id))
                cbse_roll_no = str(int(sheet.cell(row, 1).value))
                print('cbse_roll_no = %s' % str(cbse_roll_no))
                try:
                    cbse = CBSERollNo.objects.get(student=student)
                    print('cbse mapping for %s already exist. This will be updated now...' % student)
                    cbse.cbse_roll_no = str(cbse_roll_no)
                    cbse.save()
                    print('updated the cbse mapping for %s' % student)
                except Exception as e:
                    print('exception 31012020-B from exam cbse.py %s %s' % (e.message, type(e)))
                    print('cbse mapping for %s was not done till before. Doing now')
                    cbse = CBSERollNo(student=student)
                    cbse.cbse_roll_no = str(cbse_roll_no)
                    cbse.save()
                    print('created cbse mapping for %s' % student)
            except Exception as e:
                print('could not retrieve student associated with erp_id %s' % str(erp_id))
        return JSONResponse({'status': 'ok'}, status=200)


class GenerateCBSESheet(generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        school_id = request.query_params.get('school_id')
        school = School.objects.get(id=school_id)
        standard = request.query_params.get('the_class')
        the_class = Class.objects.get(school=school, standard=standard)

        cbse_file_name = 'cbse.xlsx'
        output = StringIO.StringIO(cbse_file_name)
        cbse_file = xlsxwriter.Workbook(output)

        fmt = format()
        title_format = cbse_file.add_format(fmt.get_title())
        title_format.set_border()
        header = cbse_file.add_format(fmt.get_header())
        big_font = cbse_file.add_format(fmt.get_large_font())
        big_font.set_color('#33691E')
        medium_font = cbse_file.add_format(fmt.get_medium_fong())
        medium_font.set_color('#827717')
        section_heading = cbse_file.add_format(fmt.get_section_heading())
        section_heading.set_color('#4E342E')
        cell_bold = cbse_file.add_format(fmt.get_cell_bold())
        cell_bold.set_border()
        cell_center = cbse_file.add_format(fmt.get_cell_center())
        cell_center.set_border()
        cell_left = cbse_file.add_format(fmt.get_cell_left())
        cell_left.set_border()
        cell_normal = cbse_file.add_format(fmt.get_cell_normal())
        cell_normal.set_border()

        sections = Section.objects.filter(school=school)
        subject_list = ['English', 'Hindi', 'Sanskrit', 'French', 'Mathematics', 'Science', 'Social Studies']
        for section in sections:
            students = Student.objects.filter(current_class=the_class, current_section=section)
            if students.count() > 0:
                for a_subject in subject_list:
                    print('dealing with section: %s, subject: %s' % (section, a_subject))
                    subject = Subject.objects.get(school=school, subject_name=a_subject)
                    sheet_name = '%s-%s-%s' % (the_class, section, a_subject)
                    sheet = cbse_file.add_worksheet(sheet_name)
                    sheet.set_portrait()
                    sheet.set_paper(9)
                    sheet.fit_to_pages(1, 0)
                    sheet.set_footer('&L%s&R%s' % ('Subject Teacher', 'Class Teacher as checker'))
                    sheet.set_column('A:A', 5)
                    sheet.set_column('B:B', 10)
                    sheet.set_column('C:C', 20)
                    sheet.set_column('D:I', 6)
                    sheet.set_column('J:J', 8)
                    sheet.set_column('K:M', 6)
                    sheet.set_column('N:N', 8)
                    sheet.merge_range('A1:N1', school.school_name, header)
                    sheet.merge_range('A2:N2', 'INTERNAL ASSESSMENT RECORD', header)
                    sheet.merge_range('A3:N3', 'PART I - SCHOLASTIC AREAS', header)

                    row = 3
                    col = 0
                    sheet.merge_range(row, col, row, col + 1, 'Class: %s-%s' % (the_class, section), cell_bold)
                    col += 11
                    sheet.merge_range(row, col, row, col + 2, 'Subject: %s' % a_subject, cell_bold)
                    row += 1
                    col = 0
                    sheet.merge_range(row, col, row, col + 1, 'Session: 2019-20', cell_bold)
                    col += 11
                    sheet.merge_range(row, col, row, col + 2, 'Code:____________', cell_bold)

                    row += 1
                    col = 0
                    sheet.merge_range(row, col, row + 3, col, 'S No', cell_bold)
                    col += 1
                    sheet.merge_range(row, col, row + 3, col, 'CBSE Roll No', cell_bold)
                    col += 1
                    sheet.merge_range(row, col, row + 3, col, 'Name of Student', cell_bold)
                    col += 1
                    sheet.merge_range(row, col, row, col + 6, 'Periodic Test(05)', cell_center)
                    col += 7
                    sheet.merge_range(row, col, row + 2, col, 'Note Book(5)', cell_bold)
                    col += 1
                    sheet.merge_range(row, col, row + 2, col, 'Sub Enrich ACT (5)', cell_bold)
                    col += 1
                    sheet.merge_range(row, col, row + 2, col, 'Portfolio(5)', cell_bold)
                    col += 1
                    sheet.merge_range(row, col, row + 2, col, 'Total (20)', cell_bold)
                    row += 1
                    col = 3
                    sheet.merge_range(row, col, row, col + 2, 'Marks Obtained', cell_center)
                    col += 3
                    sheet.merge_range(row, col, row, col + 2, 'Weightage', cell_center)
                    col += 3
                    sheet.merge_range(row, col, row + 1, col, 'Average of Best 2 PTS', cell_bold)
                    row += 1
                    col = 3
                    sheet.write_string(row, col, 'PT - I', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'PT-2 (HY)', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'PT-3 (PB)', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'PT - I', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'PT-2 (HY)', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'PT-3 (PB)', cell_bold)
                    row += 1
                    col = 3
                    sheet.write_string(row, col, 'Out of 30', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'Out of 80', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'Out of 80', cell_bold)
                    col += 1
                    sheet.write_string(row, col, '5%', cell_bold)
                    col += 1
                    sheet.write_string(row, col, '5%', cell_bold)
                    col += 1
                    sheet.write_string(row, col, '5%', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'A=5', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'B=5', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'C=5', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'D=5', cell_bold)
                    col += 1
                    sheet.write_string(row, col, 'A + B + C + D =20', cell_bold)

                    row = 9
                    col = 0
                    s_no = 1
                    exams = ['PT I (IX - X)', 'Term-I (IX - X)', 'Pre Board (X - XII)']
                    for student in students:
                        print('dealing with student: %s of class: %s-%s subject: %s' %
                              (student, the_class, section, a_subject))
                        sheet.write_number(row, col, s_no, cell_normal)
                        s_no += 1
                        col += 1

                        try:
                            entry = CBSERollNo.objects.get(student=student)
                            cbse_roll_no = entry.cbse_roll_no
                            sheet.write_string(row, col, cbse_roll_no, cell_normal)
                        except Exception as e:
                            print('exception 01022020-B from exam cbse.py %s %s' % (e.message, type(e)))
                            print('could not retrieve the cbse roll no for %s' % student)
                        col += 1

                        sheet.write_string(row, col, '%s %s' % (student.fist_name, student.last_name), cell_left)
                        col += 1
                        index = 1
                        for an_exam in exams:
                            exam = Exam.objects.get(school=school, title=an_exam)
                            try:
                                class_test = ClassTest.objects.get(exam=exam, subject=subject,
                                                                   the_class=the_class, section=section)
                                try:
                                    test_result = TestResults.objects.get(class_test=class_test, student=student)
                                    marks = test_result.marks_obtained
                                    sheet.write_number(row, col, marks, cell_normal)
                                    cell = xl_rowcol_to_cell(row, col)
                                    if index == 1:
                                        formula = '=ROUND(%s/6,0)' % cell
                                    else:
                                        formula = '=ROUND(%s/16,0)' % cell
                                    sheet.write_formula(row, col + 3, formula, cell_normal)
                                    index += 1

                                    if exam.exam_type == 'term':
                                        term_results = TermTestResult.objects.get(test_result=test_result)
                                        note_book = term_results.note_book_marks
                                        sheet.write_number(row, col + 6, note_book, cell_normal)
                                        sub_enrich = term_results.sub_enrich_marks
                                        sheet.write_number(row, col + 7, sub_enrich, cell_normal)
                                        portfolio = term_results.multi_asses_marks
                                        sheet.write_number(row, col + 8, portfolio, cell_normal)
                                except Exception as e:
                                    print('exception 02022020-A from exam cbse.py %s %s' % (e.message, type(e)))
                                    print('for %s, could not retrieve the marks for exam %s, subject %s ' %
                                          (student, an_exam, subject))
                                col += 1
                            except Exception as e:
                                print('exception 02022020-B from exam cbse.py %s %s' % (e.message, type(e)))
                                print('test for %s in exam %s was not scheduled' % (subject, an_exam))
                                col += 1

                        # average of best of two PTs
                        start_cell = xl_rowcol_to_cell(row, col)
                        end_cell = xl_rowcol_to_cell(row, col + 2)
                        formula = '=ROUND(SUM(LARGE(%s:%s,{1,2}))/2,0)' % (start_cell, end_cell)
                        sheet.write_formula(row, col + 3, formula, cell_normal)

                        # total out of 20 (average of best of two PTs + notebook + portfolio + sub_enrich
                        start_cell = xl_rowcol_to_cell(row, col + 3)
                        end_cell = xl_rowcol_to_cell(row, col + 6)
                        formula = '=SUM(%s:%s)' % (start_cell, end_cell)
                        sheet.write_formula(row, col + 7, formula, cell_normal)

                        row += 1
                        col = 0
        cbse_file.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s' % cbse_file_name
        response.write(output.getvalue())
        return response