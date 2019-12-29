import StringIO

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
        t1_sheet.set_paper(9)  # A4 paper
        t1_sheet.repeat_rows(1, 2)
        t1_sheet.fit_to_pages(1, 0)

        if the_class.standard not in higher_classes:
            t2_sheet = workbook.add_worksheet('Term II')
            t2_sheet.set_landscape()
            t2_sheet.set_paper(9)  # A4 paper
            t2_sheet.repeat_rows(1, 2)
            t2_sheet.fit_to_pages(1, 0)
            cons_sheet = workbook.add_worksheet('Consolidated')

        border = workbook.add_format()
        border.set_border()

        fmt = format()
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
        bold_italics.set_bg_color('#E0E0E0')
        cell_component = workbook.add_format(fmt.get_cell_component())
        cell_component.set_border()
        cell_center = workbook.add_format(fmt.get_cell_center())
        cell_center.set_border()
        vertical_text = workbook.add_format(fmt.get_vertical_text())
        vertical_text.set_border()
        cell_grade = workbook.add_format(fmt.get_cell_grade())
        cell_grade.set_bg_color('#BDBDBD')
        cell_grade2 = workbook.add_format(fmt.get_cell_grade2())
        cell_grade2.set_bg_color('#E0E0E0')
        cell_grade2.set_right(6)
        cell_right_border = workbook.add_format(fmt.get_cell_right_border())
        cell_right_border.set_right(6)
        cell_small = workbook.add_format(fmt.get_cell_small())

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
        if standard in middle_classes:
            title_range = 'A1:AM1'
        if standard in ninth_tenth:
            title_range = 'A1:AG1'
        if standard in higher_classes:
            title_range = 'A1:AO1'
        title_text = '%s \n %s Result Analysis Sheet Session 2019-20 Class %s-%s Class Teacher: %s' % \
                     (school, term1, the_class, section, class_teacher)
        t1_sheet.merge_range(title_range, title_text, title_format)
        footer_text = 'Result Analysis Sheet Class %s-%s' % (the_class, section)
        t1_sheet.set_footer('&LClass Teacher Signature&C%s&RPage &P of &N' % footer_text)
        t1_sheet.set_row(0, 35)
        t1_sheet.set_column('A:A', 2.5)
        t1_sheet.set_column('B:B', 8)
        t1_sheet.set_column('C:C', 2)

        if the_class.standard not in higher_classes:
            title_text = '%s \n %s Result Analysis Sheet Session 2019-20 Class %s-%s Class Teacher: %s' % \
                         (school, term2, the_class, section, class_teacher)
            t1_sheet.set_column('D:AM', 3)
            t2_sheet.set_footer('&LClass Teacher Signature&RPage &P of &N')
            t2_sheet.merge_range(title_range, title_text, title_format)
            t1_sheet.merge_range('A2:A3', 'S No', cell_bold)
            t1_sheet.merge_range('B2:C3', 'Student', cell_bold)
            t2_sheet.set_row(0, 35)
            t2_sheet.set_column('A:A', 2.5)
            t2_sheet.set_column('B:B', 8)
            t2_sheet.set_column('C:C', 2)
            t2_sheet.set_column('D:AM', 3)
            t2_sheet.merge_range('A2:A3', 'S No', cell_bold)
            t2_sheet.merge_range('B2:C3', 'Student', cell_bold)

        if standard in middle_classes or standard in ninth_tenth:
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
            col = 3
            for subject in subject_list:
                if subject != 'GK':
                    t1_sheet.merge_range(row, col, row, col + 4, subject, cell_right_border)
                    t2_sheet.merge_range(row, col, row, col + 4, subject, cell_right_border)

                    comp_col = col
                    for comp in components:
                        if comp == 'Mn':
                            t1_sheet.write_string(row + 1, comp_col, comp, cell_right_border)
                            t2_sheet.write_string(row + 1, comp_col, comp, cell_right_border)
                        else:
                            t1_sheet.write_string(row + 1, comp_col, comp, cell_bold)
                            t2_sheet.write_string(row + 1, comp_col, comp, cell_bold)
                        comp_col += 1
                    col += 4
                col += 1
            t1_sheet.write_string(row, col - 1, subject, cell_bold)
            t2_sheet.write_string(row, col - 1, subject, cell_bold)
            row += 1
            if standard in middle_classes:
                t1_sheet.write_string(row, col - 1, 'Gr', cell_bold)
                t2_sheet.write_string(row, col - 1, 'Gr', cell_bold)

            row += 1
            col = 0
            s_no = 1
            students = Student.objects.filter(current_class=the_class, current_section=section, active_status=True)

            for student in students:
                t1_sheet.merge_range(row, col, row + 1, col, s_no, cell_normal)
                t2_sheet.merge_range(row, col, row + 1, col, s_no, cell_normal)
                s_no += 1
                col += 1

                full_name = '%s %s' % (student.fist_name, student.last_name)
                t1_sheet.merge_range(row, col, row + 1, col, full_name, cell_bold)
                t2_sheet.merge_range(row, col, row + 1, col, full_name, cell_bold)
                col += 2

                for sub in subject_list:
                    if sub != 'GK':
                        print('now retrieving marks of subject %s for %s' % (sub, student))
                        subject = Subject.objects.get(school=school, subject_name=sub)
                        if standard in middle_classes:
                            exams = Exam.objects.filter(school=school, exam_type='term', start_class=middle_classes[0])
                        if standard in ninth_tenth:
                            exams = Exam.objects.filter(school=school, exam_type='term', start_class=ninth_tenth[0])
                        if sub == 'Third Language':
                            third_lang = ThirdLang.objects.get(student=student)
                            subject = third_lang.third_lang
                            t1_sheet.merge_range(row, 2, row + 1, 2, subject.subject_name, vertical_text)
                            t2_sheet.merge_range(row, 2, row + 1, 2, subject.subject_name, vertical_text)

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
                        main_marks = t1_marks.marks
                        if main_marks == -1000.00:
                            main_marks = 'AB'
                        if main_marks == -5000.00:
                            main_marks = 'NE'
                        t1_sheet.write(row, col, main_marks, cell_right_border)

                        main_marks = t2_marks.marks
                        if main_marks == -1000.00:
                            main_marks = 'AB'
                        if main_marks == -5000.00 or main_marks == -5000.0 or main_marks == -5000:
                            main_marks = 'NE'
                        t2_sheet.write(row, col, main_marks, cell_right_border)
                        col += 1

                        # Total & Grade
                        t1_sheet.write_string(row + 1, col - 5, 'Tot', bold_italics)
                        t2_sheet.write_string(row + 1, col - 5, 'Tot', bold_italics)
                        t1_sheet.merge_range(row + 1, col - 4, row + 1, col - 3, t1_marks.total_marks, bold_italics)
                        t2_sheet.merge_range(row + 1, col - 4, row + 1, col - 3, t2_marks.total_marks, bold_italics)

                        cell = xl_rowcol_to_cell(row + 1, col - 4, row_abs=True, col_abs=True)
                        grade_formula = '=IF(%s > 90, "A1", IF(%s > 80, "A2", IF(%s > 70, "B1", IF(%s > 60, "B2", ' \
                                        'IF(%s > 50, "C1", IF(%s > 40, "C2", IF(%s > 32, "D", "E")))))))' % \
                                        (cell, cell, cell, cell, cell, cell, cell)
                        t1_sheet.merge_range(row + 1, col - 2, row + 1, col - 1, grade_formula, cell_grade2)
                        t2_sheet.merge_range(row + 1, col - 2, row + 1, col - 1, grade_formula, cell_grade2)
                    if sub == 'GK':
                        gk = Subject.objects.get(school=school, subject_name='GK')
                        gk_tests = ClassTest.objects.filter(the_class=the_class, section=section, subject=gk)
                        t1_grade = TestResults.objects.get(class_test=gk_tests[0], student=student).grade
                        t1_sheet.merge_range(row, col, row + 1, col, t1_grade, cell_grade)
                        # t2_grade = TestResults.objects.get(class_test=gk_tests[1], student=student).grade
                        # t2_sheet.merge_range(row, col, row + 1, col, t2_grade, cell_grade)

                row += 2
                t1_sheet.set_row(row, 1.2)
                t2_sheet.set_row(row, 1.2)
                row += 1
                col = 0

        if the_class.standard in higher_classes:
            maths_stream = ['English', 'Mathematics', 'Physics', 'Chemistry', 'Elective']
            bio_stream = ['English', 'Biology', 'Physics', 'Chemistry', 'Elective']
            commerce_stream = ['English', 'Economics', 'Accountancy', 'Business Studies', 'Elective']
            humanities_stream = ['English', 'Economics', 'History', 'Sociology', 'Elective']

            students = Student.objects.filter(current_class=the_class, current_section=section, active_status=True)

            sub_dict = []
            # for higher classes we need to determine the stream selected by
            # student as well as the elective
            mapping = HigherClassMapping.objects.filter(student=students[0])
            for m in mapping:
                sub_dict.append(m.subject.subject_name)
            print('subjects chosen by %s are = ' % (students[0]))
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
                print('failed to determine the stream for class %s %s' % (the_class, section))
                print('exception 28122019-A from analytics results.py %s %s' % (e.message, type(e)))

            # row height to be adjusted to accommodate elective subject name
            # usually they are long like physical education
            for i in range(2, 140):
                t1_sheet.set_row(i, 23)

            # show 15 students one page when printed
            t1_sheet.set_h_pagebreaks([48])

            t1_sheet.set_column('C:C', 4)
            t1_sheet.set_column('D:AO', 4)
            row = 1
            col = 0
            t1_sheet.merge_range(row, col, row + 2, col, 'S No', cell_bold)
            col += 1
            t1_sheet.merge_range(row, col, row + 2, col, 'Student', cell_bold)
            col += 1
            t1_sheet.merge_range(row, col, row + 2, col, 'Elective', vertical_text)
            col += 1

            for subject in chosen_stream:
                t1_sheet.merge_range(row, col, row, col + 6, subject, cell_right_border)
                t1_sheet.merge_range(row + 1, col, row + 2, col, 'UT I', cell_bold)
                col += 1
                t1_sheet.merge_range(row + 1, col, row + 1, col + 1, 'Half Yearly', cell_bold)
                t1_sheet.write_string(row + 2, col, 'Th', cell_bold)
                t1_sheet.write_string(row + 2, col + 1, 'Pr', cell_bold)
                col += 2
                t1_sheet.merge_range(row + 1, col, row + 2, col, 'UT II', cell_bold)
                col += 1
                t1_sheet.merge_range(row + 1, col, row + 1, col + 1, 'Final', cell_bold)
                t1_sheet.write_string(row + 2, col, 'Th', cell_bold)
                t1_sheet.write_string(row + 2, col + 1, 'Pr', cell_bold)
                col += 2
                t1_sheet.merge_range(row + 1, col, row + 2, col, 'Cumul.', cell_right_border)
                col += 1
            # Grand total
            t1_sheet.merge_range(row, col, row, col + 2, 'Grand Total', cell_bold)
            t1_sheet.merge_range(row + 1, col, row + 2, col, 'Marks', cell_bold)
            col += 1
            t1_sheet.merge_range(row + 1, col, row + 2, col, '%', cell_bold)
            col += 1
            t1_sheet.merge_range(row + 1, col, row + 2, col, 'Rank', cell_bold)

            row = 4
            print('row at the time of student list = %d' % row)
            col = 0
            s_no = 1
            for student in students:
                t1_sheet.merge_range(row, col, row + 1, col, s_no, cell_bold)
                s_no += 1
                col += 1

                full_name = '%s %s' % (student.fist_name, student.last_name)
                t1_sheet.merge_range(row, col, row + 1, col, full_name, cell_bold)
                col += 1

                sub_dict = []
                mapping = HigherClassMapping.objects.filter(student=student)
                print('mapping for %s is %s' % (full_name, mapping))
                for m in mapping:
                    sub_dict.append(m.subject.subject_name)
                print('subjects chosen by %s are = ' % full_name)
                print(sub_dict)

                # now find the elective subject
                chosen_stream.pop()
                elective_sub = (set(sub_dict) ^ set(chosen_stream)).pop()
                t1_sheet.merge_range(row, col, row + 1, col, elective_sub, vertical_text)
                print('elective chosen by %s: %s' % (full_name, elective_sub))
                col += 1

                # complete the list of all subjects chosen by this student
                chosen_stream.append(elective_sub)
                print('complete list of subjects chosen by %s: ' % student)
                print(chosen_stream)

                # retrieve the marks for each subject and populate the excel
                ut_list = Exam.objects.filter(school=school, exam_type='unit', start_class='XI')

                term_list = Exam.objects.filter(school=school, exam_type='term', start_class='XI')
                for a_subject in chosen_stream:
                    print('a_subject = %s' % a_subject)
                    subject = Subject.objects.get(school=school, subject_name=a_subject)


                    # UT I marks
                    ct1 = ClassTest.objects.get(the_class=the_class, section=section, subject=subject, exam=ut_list[0])
                    ct1_result = TestResults.objects.get(class_test=ct1, student=student)
                    t1_sheet.merge_range(row, col, row + 1, col, ct1_result.marks_obtained, cell_normal)
                    col += 1

                    # half Yearly marks
                    half_yearly = SubjectAnalysis.objects.get(student=student, exam=term_list[0], subject=subject)
                    theory = half_yearly.marks
                    t1_sheet.write_number(row, col, theory, cell_normal)
                    col += 1
                    prac = half_yearly.prac_marks
                    t1_sheet.write_number(row, col, prac, cell_normal)
                    total = theory + prac
                    t1_sheet.merge_range(row + 1, col - 1, row + 1, col, total, bold_italics)
                    col += 1

                    # UT II marks
                    ct2 = ClassTest.objects.get(the_class=the_class, section=section, subject=subject, exam=ut_list[0])
                    ct2_result = TestResults.objects.get(class_test=ct2, student=student)
                    t1_sheet.merge_range(row, col, row + 1, col, ct2_result.marks_obtained, cell_normal)
                    col += 1

                    # final exam marks
                    final = SubjectAnalysis.objects.get(student=student, exam=term_list[0], subject=subject)
                    theory = final.marks
                    t1_sheet.write_number(row, col, theory, cell_normal)
                    col += 1
                    prac = final.prac_marks
                    t1_sheet.write_number(row, col, prac, cell_normal)
                    total = theory + prac
                    t1_sheet.merge_range(row + 1, col - 1, row + 1, col, total, bold_italics)
                    col += 1

                    # cumulative marksp
                    t1_sheet.merge_range(row, col, row + 1, col, ' ', cell_right_border)
                    col += 1

                row += 2
                t1_sheet.set_row(row, 1.2)
                row += 1
                col = 0

        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response
