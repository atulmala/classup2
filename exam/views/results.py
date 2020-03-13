import StringIO

from formats.formats import Formats as format

import xlsxwriter
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range

from academics.models import Class, Section, ClassTeacher, ThirdLang, Exam, Subject, ClassTest, \
    TestResults, CoScholastics
from exam.models import Scheme, HigherClassMapping, ExamResult
from analytics.models import SubjectAnalysis, StudentTotalMarks
from exam.views import get_wings
from setup.models import School
from student.models import Student


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class DetainList(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        school_id = request.query_params.get('school_id')
        school = School.objects.get(id=school_id)

        excel_file_name = 'DetainList.xlsx'
        print('excel_file_name = %s' % excel_file_name)

        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)

        t1_sheet = workbook.add_worksheet('DetainList')
        t1_sheet.set_paper(9)  # A4 paper
        t1_sheet.repeat_rows(1, 2)
        t1_sheet.fit_to_pages(1, 0)
        t1_sheet.set_row(0, 35)
        t1_sheet.set_column('A:A', 3.5)
        t1_sheet.set_column('B:B', 8)
        t1_sheet.set_column('C:C', 20)
        t1_sheet.set_column('D:D', 40)

        fmt = format()
        title_format = workbook.add_format(fmt.get_title())
        title_format.set_bg_color('#CFD8DC')
        title_format.set_border()
        title_format.set_text_wrap()
        cell_normal = workbook.add_format(fmt.get_cell_normal())
        cell_normal.set_border()
        cell_bold = workbook.add_format(fmt.get_cell_bold())
        cell_bold.set_border()
        cell_left = workbook.add_format(fmt.get_cell_left())
        cell_left.set_border()

        t1_sheet.merge_range('A1:D1', 'List of Detain/Compartment Cases', title_format)
        row = 1
        col = 0
        t1_sheet.write_string(row, col, 'S No', cell_bold)
        col += 1
        t1_sheet.write_string(row, col, 'Class', cell_bold)
        col += 1
        t1_sheet.write_string(row, col, 'Student', cell_bold)
        col += 1
        t1_sheet.write_string(row, col, 'Status', cell_bold)
        row += 1
        col = 0

        classes = Class.objects.filter(school=school).order_by('sequence')
        sections = Section.objects.filter(school=school).order_by('section')

        s_no = 1
        for a_class in classes:
            for section in sections:
                students = Student.objects.filter(current_class=a_class, current_section=section)
                for student in students:
                    try:
                        entry = ExamResult.objects.get(student=student, status=False)
                        print('student %s of %s-%s is in Detainee list' % (student, a_class, section))
                        t1_sheet.write_number(row, col, s_no)
                        s_no += 1
                        col += 1
                        t1_sheet.write_string(row, col, '%s-%s' % (a_class.standard, section.section), cell_normal)
                        col += 1
                        t1_sheet.write_string(row, col, '%s %s' % (student.fist_name, student.last_name), cell_left)
                        col += 1
                        t1_sheet.write_string(row, col, entry.detain_reason, cell_left)
                        row += 1
                        col = 0
                    except Exception as e:
                        print('exception 13032020-A from exam results.py %s %s' % (e.message, type(e)))
                        print('%s of %s-%s has passed' % (student, a_class, section))
        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response


class ResultAnalysisSheet(generics.ListCreateAPIView):
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
        middle_classes = wings['middle_classes']
        ninth_tenth = wings['ninth_tenth']
        higher_classes = wings['higher_classes']

        excel_file_name = 'Result_Analysis_Sheet_%s-%s.xlsx' % (str(the_class.standard), str(section.section))
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
            co_schol_sheet = workbook.add_worksheet('Co-scholastic Grades')
            co_schol_sheet.set_landscape()
            co_schol_sheet.set_paper(9)
            co_schol_sheet.repeat_rows(1, 0)
            co_schol_sheet.fit_to_pages(1, 0)
            cons_sheet = workbook.add_worksheet('Consolidated')
            cons_sheet.set_portrait()
            cons_sheet.set_paper(9)
            cons_sheet.repeat_rows(1, 2)
            cons_sheet.fit_to_pages(1, 0)

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
        perc_format = workbook.add_format(fmt.get_perc_format())
        rank_format = workbook.add_format(fmt.get_rank_format())
        comments_format = workbook.add_format(fmt.get_comments())

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
        if standard in middle_classes or standard in ninth_tenth:
            scheme = Scheme.objects.filter(school=school, the_class=the_class)

            # to determine upto which column stretch title, we need to know the
            # number of components based & grade based subjects in the scheme
            subject_list = []
            comp_subjects = 0
            grade_subjects = 0
            for a_subject in scheme:
                if not a_subject.subject.grade_based:
                    comp_subjects += 1
                    subject_list.append(a_subject.subject)
                else:
                    grade_subjects += 1
            print('subject_list for class %s = ' % the_class)
            print(subject_list)
            # sub_count = scheme.count() - 1
            # col_count = (sub_count * 5) + 3 # each subject 5 column, 1 each for s_no, name, elective and GK grade
            col_count = (comp_subjects * 5) + (grade_subjects * 1) + 2
            last_row_col = xl_rowcol_to_cell(0, col_count)
            title_range = 'A1:%s' % last_row_col
        if standard in ninth_tenth:
            title_range = 'A1:AG1'
        if standard in higher_classes:
            title_range = 'A1:AO1'
        title_text = '%s \n %s Result Analysis Sheet Session 2019-20 Class %s-%s Class Teacher: %s' % \
                     (school, term1, the_class, section, class_teacher)
        t1_sheet.merge_range(title_range, title_text, title_format)
        header_text = 'Result Analysis Sheet Class %s-%s' % (the_class, section)
        t1_sheet.set_header('&L%s&RPage &P of &N' % header_text)

        if the_class.standard in higher_classes:
            weightage = 'Wieghtages - Unit Tests: 25%, Half Yearly: 25% (Theory Only), Final Exam: 50% (Theory Only)'
            weightage += '. Unit test marks have been converted from out of 25'
            t1_sheet.set_footer('&LClass Teacher Signature&R%s' % weightage)
        else:
            t1_sheet.set_footer('&LClass Teacher Signature')

        t1_sheet.set_row(0, 35)
        t1_sheet.set_column('A:A', 2.5)
        t1_sheet.set_column('B:B', 8)
        t1_sheet.set_column('C:C', 2)

        if the_class.standard not in higher_classes:
            title_text = '%s \n %s Result Analysis Sheet Session 2019-20 Class %s-%s Class Teacher: %s' % \
                         (school, term2, the_class, section, class_teacher)
            t1_sheet.set_column('D:AM', 3)
            t1_sheet.merge_range('A2:A3', 'S No', cell_bold)
            t1_sheet.merge_range('B2:C3', 'Student', cell_bold)

            t2_sheet.set_header('&L%s&RPage &P of &N' % header_text)
            t2_sheet.set_footer('&LClass Teacher Signature&RPage &P of &N')
            t2_sheet.merge_range(title_range, title_text, title_format)
            t2_sheet.set_row(0, 35)
            t2_sheet.set_column('A:A', 2.5)
            t2_sheet.set_column('B:B', 8)
            t2_sheet.set_column('C:C', 2)
            t2_sheet.set_column('D:AM', 3)
            t2_sheet.merge_range('A2:A3', 'S No', cell_bold)
            t2_sheet.merge_range('B2:C3', 'Student', cell_bold)

            co_schol_title = '%s\n Co-scholastic Grades & Class Teacher Comments Class %s-%s Class Teacher: %s' % \
                             (school, the_class, section, class_teacher)
            co_schol_header = 'Co-scholastic Grades class %s-%s' % (the_class, section)
            co_schol_sheet.set_header('&L%s&RPage &P of &N' % co_schol_header)
            co_schol_sheet.set_footer('&LClass Teacher Signature&RPage &P of &N')
            co_schol_sheet.merge_range('A1:H1', co_schol_title, title_format)
            co_schol_sheet.set_row(0, 35)
            co_schol_sheet.set_column('A:A', 2.5)
            co_schol_sheet.set_column('B:B', 22)
            co_schol_sheet.set_column('G:H', 50)
            co_schol_sheet.write_string('A2', 'S No', cell_center)
            co_schol_sheet.write_string('B2', 'Student', cell_center)
            co_schol_sheet.write_string('C2', 'Work Education', cell_center)
            co_schol_sheet.write_string('D2', 'Art Education', cell_center)
            co_schol_sheet.write_string('E2', 'Health & PE', cell_center)
            co_schol_sheet.write_string('F2', 'Discipline', cell_center)
            co_schol_sheet.write_string('G2', 'Term I Class Teacher Comments', cell_center)
            co_schol_sheet.write_string('H2', 'Term II Class Teacher Comments', cell_center)

            cons_title = '%s\n Consolidated Sheet for Term I & Term II Class %s-%s Class Teacher: %s' % \
                         (school, the_class, section, class_teacher)
            cons_sheet.merge_range('A1:K1', cons_title, title_format)
            cons_header = 'Consolidated sheet class %s-%s' % (the_class, section)
            cons_sheet.set_header('&L%s' % cons_header)
            cons_sheet.set_footer('&LClass Teacher Signature&RPage &P of &N')
            cons_sheet.set_row(0, 35)
            cons_sheet.set_column('A:A', 3)
            cons_sheet.set_column('B:B', 22)
            cons_sheet.set_column('C:K', 5)
            cons_sheet.merge_range('A2:A3', 'S No', cell_center)
            cons_sheet.merge_range('B2:B3', 'Student', cell_center)
            cons_sheet.merge_range('C2:E2', 'Term I', cell_right_border)
            cons_sheet.merge_range('F2:H2', 'Term II', cell_right_border)
            cons_sheet.merge_range('I2:K2', 'Consolidated', cell_center)

            # we can use loop but who does it for just 9 iterations. Sometimes you just write it! :) :)
            cons_sheet.write_string('C3', 'Total', cell_bold)
            cons_sheet.write_string('D3', '%', cell_bold)
            cons_sheet.write_string('E3', 'Rank', cell_right_border)
            cons_sheet.write_string('F3', 'Total', cell_bold)
            cons_sheet.write_string('G3', '%', cell_bold)
            cons_sheet.write_string('H3', 'Rank', cell_right_border)
            cons_sheet.write_string('I3', 'Total', cell_bold)
            cons_sheet.write_string('J3', '%', cell_bold)
            cons_sheet.write_string('K3', 'Rank', cell_bold)

        if standard in middle_classes or standard in ninth_tenth:
            for a_subject in scheme:
                if a_subject.subject.grade_based:
                    subject_list.append(a_subject.subject)
            print('subject_list for class %s = ' % the_class)
            print(subject_list)

            # prepare subject heading
            row = 1
            col = 3
            for subject in subject_list:
                if not subject.grade_based:
                    t1_sheet.merge_range(row, col, row, col + 4, subject.subject_name, cell_right_border)
                    t2_sheet.merge_range(row, col, row, col + 4, subject.subject_name, cell_right_border)

                    components = ['PA', 'NB', 'PF', 'SE', 'Mn']
                    comp_col = col
                    for comp in components:
                        if comp == 'Mn':
                            t1_sheet.write_string(row + 1, comp_col, comp, cell_right_border)
                            t2_sheet.write_string(row + 1, comp_col, comp, cell_right_border)
                        else:
                            t1_sheet.write_string(row + 1, comp_col, comp, cell_bold)
                            t2_sheet.write_string(row + 1, comp_col, comp, cell_bold)
                        comp_col += 1
                    col += 5
                else:
                    t1_sheet.write_string(row, col, subject.subject_name, cell_bold)
                    t1_sheet.write_string(row + 1, col, 'Gr', cell_bold)
                    t2_sheet.write_string(row, col, subject.subject_name, cell_bold)
                    t2_sheet.write_string(row + 1, col, 'Gr', cell_bold)
                    col += 1

            row += 2
            col = 0
            s_no = 1
            co_schol_row = 2
            co_schol_col = 0
            cons_row = 3  # starting row for consolidated sheet
            cons_col = 0  # starting column for consolidated sheet
            students = Student.objects.filter(current_class=the_class, current_section=section, active_status=True)

            for student in students:
                t1_sheet.merge_range(row, col, row + 1, col, s_no, cell_normal)
                t2_sheet.merge_range(row, col, row + 1, col, s_no, cell_normal)
                co_schol_sheet.write_number(co_schol_row, co_schol_col, s_no, cell_normal)
                cons_sheet.write_number(cons_row, cons_col, s_no, cell_normal)
                s_no += 1
                col += 1
                co_schol_col += 1
                cons_col += 1

                full_name = '%s %s' % (student.fist_name, student.last_name)
                t1_sheet.merge_range(row, col, row + 1, col, full_name, cell_bold)
                t2_sheet.merge_range(row, col, row + 1, col, full_name, cell_bold)
                col += 2

                co_schol_sheet.write_string(co_schol_row, co_schol_col, full_name, cell_bold)
                co_schol_col += 1

                if standard in middle_classes:
                    exams = Exam.objects.filter(school=school, exam_type='term', start_class=middle_classes[0])
                if standard in ninth_tenth:
                    exams = Exam.objects.filter(school=school, exam_type='term', start_class=ninth_tenth[0])

                cons_sheet.write_string(cons_row, cons_col, full_name, cell_bold)
                cons_col += 1

                t1_summary = StudentTotalMarks.objects.get(student=student, exam=exams[0])
                t1_total = t1_summary.total_marks
                cons_sheet.write_number(cons_row, cons_col, t1_total, cell_normal)
                cons_col += 1
                t1_perc = float(t1_summary.percentage) / 100.00
                cons_sheet.write_number(cons_row, cons_col, t1_perc, perc_format)
                cons_col += 1
                t1_rank = t1_summary.rank
                cons_sheet.write_number(cons_row, cons_col, t1_rank, cell_right_border)
                cons_col += 1

                t2_summary = StudentTotalMarks.objects.get(student=student, exam=exams[1])  # todo change to exams[1]
                t2_total = t2_summary.total_marks
                cons_sheet.write_number(cons_row, cons_col, t2_total, cell_normal)
                cons_col += 1
                t2_perc = float(t2_summary.percentage) / 100.00
                cons_sheet.write_number(cons_row, cons_col, t2_perc, perc_format)
                cons_col += 1
                t2_rank = t2_summary.rank
                cons_sheet.write_number(cons_row, cons_col, t2_rank, cell_right_border)
                cons_col += 1

                t1_t2_total = t1_total + t2_total
                cons_sheet.write_number(cons_row, cons_col, t1_t2_total, cell_normal)
                cons_col += 1
                t1_t2_perc = float((t1_perc + t2_perc) / 2)
                cons_sheet.write_number(cons_row, cons_col, t1_t2_perc, perc_format)
                cons_col += 1

                # rank for both term consolidated will have to be calculated via inserting excel formula
                count = students.count()
                start_row = 4
                formula = '=RANK(I%s, $I$%s:$I$%s)' % (str(cons_row + 1), str(start_row), str(count + 4))
                print('formula for rank: %s', formula)
                cons_sheet.write_formula(cons_row, cons_col, formula, rank_format)

                cons_row += 1
                cons_col = 0

                for sub in subject_list:
                    subject = Subject.objects.get(school=school, subject_name=sub)
                    if not subject.grade_based:
                        print('now retrieving marks of subject %s for %s' % (sub, student))
                        if sub.subject_name == 'Third Language':
                            third_lang = ThirdLang.objects.get(student=student)
                            subject = third_lang.third_lang
                            t1_sheet.merge_range(row, 2, row + 1, 2, subject.subject_name, vertical_text)
                            t2_sheet.merge_range(row, 2, row + 1, 2, subject.subject_name, vertical_text)

                        t1_marks = SubjectAnalysis.objects.get(student=student, exam=exams[0], subject=subject)
                        t2_marks = SubjectAnalysis.objects.get(student=student, exam=exams[1], subject=subject)

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
                    else:
                        # gk = Subject.objects.get(school=school, subject_name='GK')
                        gk_tests = ClassTest.objects.filter(the_class=the_class, section=section, subject=subject)
                        t1_grade = TestResults.objects.get(class_test=gk_tests[0], student=student).grade
                        t1_sheet.merge_range(row, col, row + 1, col, t1_grade, cell_grade)
                        t2_grade = TestResults.objects.get(class_test=gk_tests[1], student=student).grade
                        t2_sheet.merge_range(row, col, row + 1, col, t2_grade, cell_grade)
                row += 2
                t1_sheet.set_row(row, 1.2)
                t2_sheet.set_row(row, 1.2)
                row += 1
                col = 0

                # 04/04/2020 - co-scholastic grades and teacher comments
                work_ed = ''
                art_ed = ''
                health = ''
                discipline = ''
                t1_remarks = ''
                t2_remarks = ''

                try:
                    t1_co_schol = CoScholastics.objects.get(student=student, term='term1')
                    work_ed = t1_co_schol.work_education
                    art_ed = t1_co_schol.art_education
                    health = t1_co_schol.health_education
                    discipline = t1_co_schol.discipline
                    t1_remarks = t1_co_schol.teacher_remarks
                except Exception as e:
                    print('exception 04042020-A from exam results.py %s %s' % (e.message, type(e)))
                    print('could not retrieve term I co-scholastic grades for %s of %s-%s' %
                          (student, the_class, section))

                try:
                    t2_co_schol = CoScholastics.objects.get(student=student, term='term2')
                    work_ed += ' / %s' % t2_co_schol.work_education
                    art_ed += ' / %s' % t2_co_schol.art_education
                    health += ' / %s' % t2_co_schol.health_education
                    discipline += ' / %s' % t2_co_schol.discipline
                    t2_remarks = t2_co_schol.teacher_remarks
                except Exception as e:
                    print('exception 04042020-A from exam results.py %s %s' % (e.message, type(e)))
                    print('could not retrieve term II co-scholastic grades for %s of %s-%s' %
                          (student, the_class, section))

                co_schol_sheet.write_string(co_schol_row, co_schol_col, work_ed, cell_bold)
                co_schol_col += 1
                co_schol_sheet.write_string(co_schol_row, co_schol_col, art_ed, cell_bold)
                co_schol_col += 1
                co_schol_sheet.write_string(co_schol_row, co_schol_col, health, cell_bold)
                co_schol_col += 1
                co_schol_sheet.write_string(co_schol_row, co_schol_col, discipline, cell_bold)
                co_schol_col += 1
                co_schol_sheet.write_string(co_schol_row, co_schol_col, t1_remarks, comments_format)
                co_schol_col += 1
                co_schol_sheet.write_string(co_schol_row, co_schol_col, t2_remarks, comments_format)

                co_schol_row += 1
                co_schol_col = 0

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
            # print('subjects chosen by %s are = ' % (students[0]))
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
            t1_sheet.set_h_pagebreaks([39])

            t1_sheet.set_column('C:C', 4)
            t1_sheet.set_column('D:AL', 3)
            t1_sheet.set_column('AM:AN', 5)
            t1_sheet.set_column('AO:AO', 4)
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
                t1_sheet.merge_range(row + 1, col, row + 2, col, 'UT I\n30', cell_bold)
                col += 1
                t1_sheet.merge_range(row + 1, col, row + 1, col + 1, 'Half Yearly', cell_bold)
                t1_sheet.write_string(row + 2, col, 'Th', cell_bold)
                t1_sheet.write_string(row + 2, col + 1, 'Pr', cell_bold)
                col += 2
                t1_sheet.merge_range(row + 1, col, row + 2, col, 'UT II\n80', cell_bold)
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
                # print('subjects chosen by %s are = ' % full_name)
                # print(sub_dict)

                # now find the elective subject
                chosen_stream.pop()
                elective_sub = (set(sub_dict) ^ set(chosen_stream)).pop()
                t1_sheet.merge_range(row, col, row + 1, col, elective_sub, vertical_text)
                print('elective chosen by %s: %s' % (full_name, elective_sub))
                col += 1

                # complete the list of all subjects chosen by this student
                chosen_stream.append(elective_sub)
                # print('complete list of subjects chosen by %s: ' % student)
                # print(chosen_stream)

                # retrieve the marks for each subject and populate the excel
                grand_total = 0.0
                ut_list = Exam.objects.filter(school=school, exam_type='unit', start_class='XI')

                term_list = Exam.objects.filter(school=school, exam_type='term', start_class='XI')
                for a_subject in chosen_stream:
                    print('a_subject = %s' % a_subject)
                    subject = Subject.objects.get(school=school, subject_name=a_subject)

                    cumul = 0.0

                    # UT I marks
                    ut1 = ClassTest.objects.get(the_class=the_class, section=section, subject=subject, exam=ut_list[0])
                    ut1_result = TestResults.objects.get(class_test=ut1, student=student)
                    ut1_marks = ut1_result.marks_obtained
                    if ut1_marks > -1000.0:
                        max_marks = ut1.max_marks
                        out_of_25 = (25.0 * float(ut1_marks)) / float(max_marks)
                        # t1_sheet.merge_range(row, col, row + 1, col, out_of_25, cell_normal)
                        t1_sheet.merge_range(row, col, row + 1, col, ut1_marks, cell_normal)
                        cumul += out_of_25 / 2.0
                    else:
                        if ut1_marks == -1000.0 or ut1_marks == -1000.00:
                            t1_sheet.merge_range(row, col, row + 1, col, 'ABS', vertical_text)
                        if ut1_marks == -5000.0 or ut1_marks == -5000.00:
                            t1_sheet.merge_range(row, col, row + 1, col, 'TBE', vertical_text)
                    col += 1

                    # half Yearly marks
                    half_yearly = SubjectAnalysis.objects.get(student=student, exam=term_list[0], subject=subject)
                    theory = half_yearly.marks
                    if theory > -1000.0:
                        t1_sheet.write_number(row, col, theory, cell_normal)
                        max_marks = subject.theory_marks
                        cumul += (float(theory) * 25.0) / float(max_marks)  # 25% weightage of half yearly theory marks
                    else:
                        if theory == -1000.0 or theory == -1000.00:
                            t1_sheet.write_string(row, col, 'ABS', vertical_text)
                        if theory == -5000.0 or theory == -5000.00:
                            t1_sheet.write_string(row, col, 'TBE', vertical_text)
                    col += 1
                    prac = half_yearly.prac_marks
                    t1_sheet.write_number(row, col, prac, cell_normal)
                    total = theory + prac
                    t1_sheet.merge_range(row + 1, col - 1, row + 1, col, total, bold_italics)
                    col += 1

                    # UT II marks
                    ut2 = ClassTest.objects.get(the_class=the_class, section=section, subject=subject, exam=ut_list[1])
                    ut2_result = TestResults.objects.get(class_test=ut2, student=student)
                    ut2_marks = ut2_result.marks_obtained  # todo - change to ut2 later
                    if ut2_marks > -1000.0:
                        max_marks = ut2.max_marks
                        out_of_25 = (25.0 * float(ut2_marks)) / float(max_marks)
                        # t1_sheet.merge_range(row, col, row + 1, col, out_of_25, cell_normal)
                        t1_sheet.merge_range(row, col, row + 1, col, ut2_marks, cell_normal)
                        cumul += out_of_25 / 2.0
                    else:
                        if ut2_marks == -1000.0 or ut2_marks == -1000.00:
                            t1_sheet.merge_range(row, col, row + 1, col, 'ABS', vertical_text)
                        if ut2_marks == -5000.0 or ut2_marks == -5000.00:
                            t1_sheet.merge_range(row, col, row + 1, col, 'TBE', vertical_text)
                    col += 1

                    # final exam marks
                    final = SubjectAnalysis.objects.get(student=student, exam=term_list[1], subject=subject)
                    theory = final.marks
                    if theory > -1000.0:
                        t1_sheet.write_number(row, col, theory, cell_normal)
                        max_marks = subject.theory_marks
                        cumul += (float(theory) * 50.0) / float(max_marks)  # 50% weightage of final exam theory marks

                    else:
                        if theory == -1000.0 or theory == -1000.00:
                            t1_sheet.write_string(row, col, 'ABS', vertical_text)
                        if theory == -5000.0 or theory == -5000.00:
                            t1_sheet.write_string(row, col, 'TBE', vertical_text)
                    col += 1
                    prac = final.prac_marks
                    t1_sheet.write_number(row, col, prac, cell_normal)
                    total = theory + prac
                    t1_sheet.merge_range(row + 1, col - 1, row + 1, col, total, bold_italics)
                    col += 1

                    # cumulative marks
                    t1_sheet.merge_range(row, col, row + 1, col, cumul, cell_right_border)
                    grand_total += cumul
                    col += 1
                t1_sheet.merge_range(row, col, row + 1, col, grand_total, cell_bold)
                col += 1
                percentage = (grand_total / 500.00)
                t1_sheet.merge_range(row, col, row + 1, col, percentage, perc_format)
                col += 1

                # determine the rank. Two rows are consumed by each student plus a blank narrow row for margin
                count = students.count()
                start_row = 3
                formula = '=RANK(AM%s, $AM$%s:$AM$%s)' % (str(row + 1), str(start_row), str(count * 3 + 3))
                print('formula for rank: %s', formula)
                t1_sheet.merge_range(row, col, row + 1, col, formula, rank_format)

                row += 2
                t1_sheet.set_row(row, 1.2)
                row += 1
                col = 0

        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response
