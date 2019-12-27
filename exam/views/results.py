import StringIO
import json
from decimal import Decimal
from formats.formats import Formats as format

import xlsxwriter
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range

from academics.models import Class, Section, ClassTeacher, ThirdLang, Exam, Subject, ClassTest, TestResults, \
    TermTestResult, CoScholastics
from exam.models import Scheme, NPromoted, HigherClassMapping
from analytics.models import SubjectAnalysis, StudentTotalMarks
from exam.views import get_wings
from setup.models import School
from student.models import Student, House


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


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
        t1_sheet = workbook.add_worksheet('Term I')
        t1_sheet.set_landscape()
        t2_sheet = workbook.add_worksheet('Term II')
        t2_sheet.set_landscape()
        t1_sheet.repeat_rows(1, 2)
        t2_sheet.repeat_rows(1, 2)
        t1_sheet.fit_to_pages(1, 0)
        t2_sheet.fit_to_pages(1, 0)
        cons_sheet = workbook.add_worksheet('Consolidated')

        border = workbook.add_format()
        border.set_border()

        fmt = format()
        title = workbook.add_format(fmt.get_title())
        header = workbook.add_format(fmt.get_header())

        title_format = workbook.add_format(fmt.get_title())
        title_format.set_bg_color('#CFD8DC')
        title_format.set_border()
        title_format.set_text_wrap()
        cell_normal = workbook.add_format(fmt.get_cell_normal())
        cell_normal.set_border()
        cell_bold = workbook.add_format(fmt.get_cell_bold())
        cell_bold.set_border()
        bold_italics = workbook.add_format(fmt.get_bold_italics())
        bold_italics.set_border()
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

        # get the name of the class teacher
        class_teacher = 'N/A'
        try:
            ct = ClassTeacher.objects.get(school=school, standard=the_class, section=section)
            class_teacher = '%s %s' % (ct.class_teacher.first_name, ct.class_teacher.last_name)
            print ('class teacher for class %s-%s is %s' %
                   (the_class.standard, section.section, class_teacher))
        except Exception as e:
            print ('exception 24122019-A from exam results.py %s %s' % (e.message, type(e)))
            print ('class teacher for class %s-%s is not set!' % (the_class.standard, section.section))

        term1 = 'Term I'
        term2 = 'Term II'
        title_text = '%s \n %s Result Analysis Sheet Session 2019-20 Class %s-%s Class Teacher: %s' % \
                     (school, term1, the_class, section, class_teacher)
        t1_sheet.merge_range('A1:AL1', title_text, title_format)
        title_text = '%s \n %s Result Analysis Sheet Session 2019-20 Class %s-%s Class Teacher: %s' % \
                     (school, term2, the_class, section, class_teacher)
        t2_sheet.merge_range('A1:AL1', title_text, title_format)
        t1_sheet.set_row(0, 35)
        t2_sheet.set_row(0, 35)
        t1_sheet.set_column('A:A', 4)
        t2_sheet.set_column('A:A', 4)
        t1_sheet.set_column('B:B', 8)
        t2_sheet.set_column('B:B', 8)
        t1_sheet.set_column('C:AS', 3)
        t2_sheet.set_column('C:AL', 3)

        t1_sheet.merge_range('A2:A3', 'S No.', cell_bold)
        t2_sheet.merge_range('A2:A3', 'S No.', cell_bold)
        t1_sheet.merge_range('B2:B3', 'Student', cell_bold)
        t2_sheet.merge_range('B2:B3', 'Student', cell_bold)

        if standard in middle_classes:
            scheme = Scheme.objects.filter(school=school, the_class=the_class)
            components = ['PA', 'NB', 'PF', 'SE', 'Mn']
            subject_list = []
            for a_subject in scheme:
                subject_list.append(a_subject.subject.subject_name)
                print('subject_list for class %s = ' % the_class)
                print(subject_list)

            # GK should be at the end of subject list as it is grade based and does not have breakup components
            if 'GK' in subject_list:
                subject_list.remove('GK')  # remove GK from whichever position it was in the list
                subject_list.append('GK')  # append at the end
                print('now GK should be at the end of subject list')
                print(subject_list)

            # prepare subject heading
            row = 1
            col = 2
            for subject in subject_list:
                if subject != 'GK':
                    t1_sheet.merge_range(row, col, row, col + 4, subject, cell_center)
                    t2_sheet.merge_range(row, col, row, col + 4, subject, cell_center)

                    comp_col = col
                    for comp in components:
                        t1_sheet.write_string(row + 1, comp_col, comp, cell_bold)
                        t2_sheet.write_string(row + 1, comp_col, comp, cell_bold)
                        comp_col += 1
                    col += 4
                col += 1
            t1_sheet.write_string(row, col - 1, subject, cell_bold)
            t2_sheet.write_string(row, col - 1, subject, cell_bold)
            row += 1
            t1_sheet.write_string(row, col - 1, 'Gr', cell_bold)
            t2_sheet.write_string(row, col - 1, 'Gr', cell_bold)

            row += 1
            col = 0
            s_no = 1
            students = Student.objects.filter(current_class=the_class, current_section=section)
            for student in students:
                t1_sheet.merge_range(row, col, row + 1, col, s_no, cell_normal)
                t2_sheet.merge_range(row, col, row + 1, col, s_no, cell_normal)
                s_no += 1
                col += 1

                full_name = '%s %s' % (student.fist_name, student.last_name)
                t1_sheet.merge_range(row, col, row + 1, col, full_name, cell_bold)
                t2_sheet.merge_range(row, col, row + 1, col, full_name, cell_bold)
                col += 1

                for sub in subject_list:
                    if sub != 'GK':
                        print('now retrieving marks of subject %s for %s' % (sub, student))
                        subject = Subject.objects.get(school=school, subject_name=sub)
                        exams = Exam.objects.filter(school=school, exam_type='term')

                        if sub == 'Third Language':
                            third_lang = ThirdLang.objects.get(student=student)
                            subject = third_lang.third_lang

                        t1_marks = SubjectAnalysis.objects.get(student=student, exam=exams[0], subject=subject)
                        t2_marks = SubjectAnalysis.objects.get(student=student, exam=exams[0], subject=subject)

                        # PA
                        t1_sheet.write_number(row, col, t1_marks.periodic_test_marks, cell_normal)
                        t2_sheet.write_number(row, col, t2_marks.periodic_test_marks, cell_normal)
                        col += 1

                        # MA
                        t1_sheet.write_number(row, col, t1_marks.multi_asses_marks, cell_normal)
                        t2_sheet.write_number(row, col, t2_marks.multi_asses_marks, cell_normal)
                        col += 1

                        # PF
                        t1_sheet.write_number(row, col, t1_marks.portfolio_marks, cell_normal)
                        t2_sheet.write_number(row, col, t2_marks.portfolio_marks, cell_normal)
                        col += 1

                        # SE
                        t1_sheet.write_number(row, col, t1_marks.sub_enrich_marks, cell_normal)
                        t2_sheet.write_number(row, col, t2_marks.sub_enrich_marks, cell_normal)
                        col += 1

                        # Mn
                        t1_sheet.write_number(row, col, t1_marks.marks, cell_normal)
                        t2_sheet.write_number(row, col, t2_marks.marks, cell_normal)
                        col += 1

                        # Total & Grade
                        # col -= 5
                        # row += 1
                        t1_sheet.write_string(row + 1, col - 5, 'Tot', bold_italics)
                        t2_sheet.write_string(row + 1, col - 5, 'Tot', bold_italics)
                        # col += 1
                        t1_sheet.merge_range(row + 1, col - 4, row + 1, col - 3, t1_marks.total_marks, bold_italics)
                        t2_sheet.merge_range(row + 1, col - 4, row + 1, col - 3, t2_marks.total_marks, bold_italics)

                        cell = xl_rowcol_to_cell(row + 1, col - 4, row_abs=True, col_abs=True)
                        grade_formula = '=IF(%s > 90, "A1", IF(%s > 80, "A2", IF(%s > 70, "B1", ' \
                                        'IF(%s > 60, "B2", ' \
                                        'IF(%s > 50, "C1", IF(%s > 40, "C2", IF(%s > 32, "D", "E")))))))' % \
                                        (cell, cell, cell, cell, cell, cell, cell)
                        print('grade_formula = %s' % grade_formula)
                        # col += 2
                        t1_sheet.merge_range(row + 1, col - 2, row + 1, col - 1, grade_formula, cell_grade)
                        t2_sheet.merge_range(row + 1, col - 2, row + 1, col - 1, grade_formula, cell_grade)
                        # col += 2

                row += 2
                col = 0

        # if the_class.standard in higher_classes:
        #     maths_stream = ['English', 'Mathematics', 'Physics', 'Chemistry', 'Elective']
        #     bio_stream = ['English', 'Biology', 'Physics', 'Chemistry', 'Elective']
        #     commerce_stream = ['English', 'Economics', 'Accountancy', 'Business Studies', 'Elective']
        #     humanities_stream = ['English', 'Economics', 'History', 'Sociology', 'Elective']
        #     components = ['UT', 'Half Yearly', 'Final Exam', 'Cumulative']

        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response
