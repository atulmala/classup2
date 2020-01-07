import StringIO
import ast
from decimal import Decimal

import statistics
import xlsxwriter

from django.db.models import Sum, Count
from django.http import HttpResponse
from reportlab.lib.colors import black
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from xlsxwriter.utility import xl_rowcol_to_cell, xl_range

from authentication.views import JSONResponse

from setup.models import School
from student.models import Student, House
from academics.models import Class, Section, Subject, Exam, ClassTest, TestResults, TermTestResult, ClassTeacher, \
    ThirdLang, CoScholastics
from exam.models import Wing, Marksheet, Scheme, NPromoted, HigherClassMapping
from exam.views import get_wings
from formats.formats import Formats as format
from analytics.models import SubjectAnalysis, SubjectHighestAverage, ExamHighestAverage, StudentTotalMarks


# Create your views here.


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class CalculateStudentTotalMarks(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)

        exams = Exam.objects.filter(school=school, exam_type='term')

        students = Student.objects.filter(school=school)

        for exam in exams:
            for student in students:
                total_marks = SubjectAnalysis.objects.filter(exam=exam, student=student).aggregate(Sum('total_marks'))
                if total_marks['total_marks__sum'] is not None:
                    print(total_marks)
                    subject_count = SubjectAnalysis.objects.filter(exam=exam,
                                                                   student=student).aggregate(Count('total_marks'))
                    print(subject_count)
                    grand_total = subject_count['total_marks__count'] * 100.00
                    print('grand total = %.2f' % grand_total)
                    try:
                        student_total_marks = StudentTotalMarks.objects.get(exam=exam, student=student)
                        student_total_marks.total_marks = total_marks['total_marks__sum']
                        percentage = (float(total_marks['total_marks__sum'])/float(grand_total)) * 100
                        student_total_marks.percentage = float(percentage)
                        student_total_marks.save()
                        print('total marks & percentage for %s of %s-%s in %s are updated' %
                              (student, student.current_class, student.current_section, exam))
                    except Exception as e:
                        print('exception 28102019-A from analytics views.py %s %s' % (e.message, type(e)))
                        student_total_marks = StudentTotalMarks(exam=exam, student=student)
                        student_total_marks.total_marks = total_marks['total_marks__sum']
                        percentage = (float(total_marks['total_marks__sum']) / float(grand_total)) * 100
                        student_total_marks.percentage = float(percentage)
                        student_total_marks.save()
                        print('total marks for %s of %s-%s in %s are created' %
                              (student, student.current_class, student.current_section, exam))
        context_dict['outcome'] = 'success'
        return JSONResponse(context_dict, status=200)


class CalculateStudentRank(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {
        }
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        students = Student.objects.filter(school=school)
        exams = Exam.objects.filter(school=school, exam_type='term')

        for student in students:
            the_class = student.current_class
            section = student.current_section
            for exam in exams:
                marks_list = StudentTotalMarks.objects.filter(
                    exam=exam, student__current_class=the_class, student__current_section=section).\
                    order_by('-total_marks').values_list('total_marks', flat=True)
                if len(marks_list) > 0:
                    try:
                        print('determining rank of %s of %s-%s in exam %s' % (student, the_class, section, exam))
                        student_marks = StudentTotalMarks.objects.get(exam=exam, student=student)
                        my_marks = student_marks.total_marks
                        print('marks obtained by %s = %.2f' % (student, my_marks))
                        rank =list(marks_list).index(my_marks) + 1
                        out_of = len(marks_list)
                        print('rank secured by %s = %d / %d' % (student, rank, out_of))
                        student_marks.rank = rank
                        student_marks.out_of = out_of
                        student_marks.save()
                    except Exception as e:
                        print('exception 31102019-A from analytics views.py %s %s' % (e.message, type(e)))
                        print('error while determining rank of %s of %s-%s in %s' %
                              (student, the_class, section, exam))
        context_dict['outcome'] = 'success'
        return JSONResponse(context_dict, status=200)


class ClassHighestAverage(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)

        classes = Class.objects.filter(school=school)
        sections = Section.objects.filter(school=school)
        exams = Exam.objects.filter(school=school, exam_type='term')

        for exam in exams:
            print('dealing with exam %s' % exam)
            for a_class in classes:
                for section in sections:
                    students = Student.objects.filter(current_class=a_class, current_section=section)
                    student_marks_array = []
                    for student in students:
                        try:
                            this_student_total = SubjectAnalysis.objects.filter(
                                exam=exam, student=student).aggregate(Sum('total_marks'))
                            if this_student_total['total_marks__sum'] is not None:
                                student_marks_array.append(this_student_total['total_marks__sum'])
                                print(student_marks_array)
                        except Exception as e:
                            print('exception 27102019-P from analytics views.py %s %s' % (e.message, type(e)))
                            print('analysis in class %s-%s for %s in exam %s not yet created' %
                                  (a_class, section, student, exam))
                            continue
                    try:
                        exam_high = ExamHighestAverage.objects.get(exam=exam, the_class=a_class, section=section)
                        exam_high.highest = max(student_marks_array)
                        exam_high.average = statistics.mean(student_marks_array)
                        exam_high.save()
                        print('updated highest/average for %s class %s-%s' % (exam, a_class, section))
                    except Exception as e:
                        print('exception 27102019-Q from analytic views.py %s %s' % (e.message, type(e)))
                        print('highest/average for %s class %s-%s generating' % (exam, a_class, section))
                        exam_high = ExamHighestAverage(exam=exam, the_class=a_class, section=section)
                        if len(student_marks_array) > 0:
                            exam_high.highest = max(student_marks_array)
                            exam_high.average = statistics.mean(student_marks_array)
                            exam_high.save()
                            print('created highest/average for %s class %s-%s' % (exam, a_class, section))
        context_dict['outcome'] = 'success'
        return JSONResponse(context_dict, status=200)


class GenerateSubAnalysis(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)

        classes = Class.objects.filter(school=school)
        sections = Section.objects.filter(school=school)
        exams = Exam.objects.filter(school=school, exam_type='term')
        print('exams = ')
        print(exams)

        wings = get_wings(school)
        junior_classes = wings['junior_classes']
        middle_classes = wings['middle_classes']
        ninth_tenth = wings['ninth_tenth']
        higher_classes = wings['higher_classes']

        for exam in exams:
            print('dealing with exam %s' % exam)
            for a_class in classes:
                for section in sections:
                    # first get the highest and average for each subject taught in this class
                    tests = ClassTest.objects.filter(exam=exam, the_class=a_class, section=section)
                    print('tests under %s for class %s-%s' % (exam, a_class, section))
                    print(tests)
                    for test in tests:
                        marks_array = []
                        subject = test.subject

                        print('finding the highest and calculating average marks in %s class %s-%s' %
                              (subject, a_class, section))
                        results = TestResults.objects.filter(class_test=test, marks_obtained__gte=0.0)
                        total = 0.0
                        for result in results:
                            total += float(result.marks_obtained)
                            print('total just from theory exam = %.2f' % total)
                            term_results = TermTestResult.objects.get(test_result=result)
                            print('term_results = ')
                            print(term_results)

                            if (a_class.standard in middle_classes) or (a_class in ninth_tenth):
                                pa_marks = float(term_results.periodic_test_marks)
                                mult_asses = float(term_results.multi_asses_marks)
                                notebook = float(term_results.note_book_marks)
                                sub_enrich = float(term_results.sub_enrich_marks)
                                total += pa_marks + mult_asses + notebook + sub_enrich
                                print('total after adding other components = %.2f' % total)

                            if a_class.standard in higher_classes:
                                prac_marks = float(term_results.prac_marks)
                                total += prac_marks
                                print('total after adding other components = %.2f' % total)

                            if total > 0.0:
                                marks_array.append(total)
                                total = 0.0
                        print(marks_array)

                        # 16/12/2019- some stupid teachers create tests even for the junior classes like Nursery, KG
                        # but does not enter marks
                        try:
                            average = statistics.mean(marks_array)
                            highest = max(marks_array)
                        except Exception as e:
                            print('exception 16122019-A from analytics views.py %s %s' % (e.message, type(e)))
                            print('marks not entered for this test')
                            average = 0.0
                            highest = 0.0

                        try:
                            sub_high_avg = SubjectHighestAverage.objects.get(exam=exam, the_class=a_class,
                                                                             section=section, subject=subject)
                            sub_high_avg.average = average
                            sub_high_avg.highest = highest
                            sub_high_avg.save()
                            print('updated average highest for %s class %s-%s' % (subject, a_class, section))
                        except Exception as e:
                            print('exception 26102019-E from analytics views.py %s %s' % (e.message, type(e)))
                            print('average & highest not yet determined for %s class %s-%s. Doing now...' %
                                  (subject, a_class, section))
                            sub_high_avg = SubjectHighestAverage(exam=exam, the_class=a_class,
                                                                 section=section, subject=subject)
                            sub_high_avg.average = average
                            sub_high_avg.highest = highest
                            sub_high_avg.save()
                            print('created average highest for %s class %s-%s' % (subject, a_class, section))
        print('generating analytics for %s-%s' % (a_class, section))
        students = Student.objects.filter(school=school)
        for student in students:
            for exam in exams:
                tests = ClassTest.objects.filter(exam=exam, the_class=student.current_class,
                                                 section=student.current_section)
                print(tests)
                for test in tests:
                    subject = test.subject
                    try:
                        test_result = TestResults.objects.get(class_test=test, student=student)
                        marks = float(test_result.marks_obtained)

                        term_results = TermTestResult.objects.get(test_result=test_result)
                        if student.current_class.standard not in higher_classes:
                            pa_marks = float(term_results.periodic_test_marks)
                            mult_asses = float(term_results.multi_asses_marks)
                            notebook = float(term_results.note_book_marks)
                            sub_enrich = float(term_results.sub_enrich_marks)
                            total_marks = marks + pa_marks + mult_asses
                            total_marks += notebook + sub_enrich

                        if student.current_class.standard in higher_classes:
                            prac_marks = float(term_results.prac_marks)
                            total_marks = marks + prac_marks

                        if total_marks < 0.0:
                            total_marks = 0.0

                        print('total marks for %s in %s of %s-%s = %.2f' %
                              (student, subject, student.current_class,
                               student.current_section, total_marks))
                        try:
                            highest_average = SubjectHighestAverage.objects.get(exam=exam,
                                                                                the_class=student.current_class,
                                                                                section=student.current_section,
                                                                                subject=subject)
                            highest = highest_average.highest
                            average = highest_average.average

                            # get the highest and average marks in this subject for this exam
                            try:
                                analytics = SubjectAnalysis.objects.get(student=student, exam=exam,
                                                                        subject=subject)
                                analytics.marks = marks
                                if student.current_class.standard not in higher_classes:
                                    analytics.periodic_test_marks = pa_marks
                                    analytics.multi_asses_marks = mult_asses
                                    analytics.portfolio_marks = notebook
                                    analytics.sub_enrich_marks = sub_enrich
                                else:
                                    analytics.prac_marks = prac_marks

                                analytics.total_marks = total_marks
                                analytics.highest = highest
                                analytics.average = average
                                analytics.save()
                                print('updated highest & average for %s in exam %s' % (subject, exam))
                            except Exception as e:
                                print('exception 26102019-B from analytics views.py %s %s' %
                                      (e.message, type(e)))
                                print('analytics for %s in %s for %s-%s not yet created. Creating now..' %
                                      (student, subject, student.current_class, student.current_section))
                                analytics = SubjectAnalysis(student=student, exam=exam, subject=subject)
                                analytics.marks = marks
                                if student.current_class.standard not in higher_classes:
                                    analytics.periodic_test_marks = pa_marks
                                    analytics.multi_asses_marks = mult_asses
                                    analytics.portfolio_marks = notebook
                                    analytics.sub_enrich_marks = sub_enrich
                                else:
                                    analytics.prac_marks = prac_marks
                                analytics.total_marks = total_marks
                                analytics.highest = highest
                                analytics.average = average
                                analytics.save()
                                print('created highest & average for %s in exam %s' % (subject, exam))
                        except Exception as e:
                            print('exception 26102019-C from analytics views.py %s %s' %
                                  (e.message, type(e)))
                            print('highest & average marks not yet determined for %s in exam %s' %
                                  (subject, exam))

                    except Exception as e:
                        print('exception 27102019-A from analytics.py %s %s' % (e.message, type(e)))
                        print('failed to retrieve test/term results for %s in %s %s-%s' %
                              (student, subject, student.current_class, student.current_section))
        context_dict['outcome'] = 'success'
        return JSONResponse(context_dict, status=200)


class StudentPerformanceAnalysis(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        school_id = request.query_params.get('school_id')
        school = School.objects.get(id=school_id)
        school_name = school.school_name
        school_address = school.school_address
        standard = request.query_params.get('the_class')
        the_class = Class.objects.get(school=school, standard=standard)
        sec = request.query_params.get('section')
        section = Section.objects.get(school=school, section=sec)
        selected_student = request.query_params.get('student')

        whole_class = True

        if selected_student != 'na':
            whole_class = False
            adm_no = selected_student.partition('(')[-1].rpartition(')')[0]
            print('admission/registration no is %s' % adm_no)
            s = Student.objects.get(school=school, student_erp_id=adm_no)
            print(s)
            selected_student = ('%s_%s' % (s.fist_name, s.last_name))
            students = [s]
            print('selected_student now = %s' % selected_student)
            pdf_name = ('%s_%s_Performance_Analyis.pdf' % (s.fist_name, s.last_name))

        if whole_class:
            pdf_name = '%s-%s%s' % (standard, sec, '_Performance_Analysis.pdf')
            students = Student.objects.filter(current_class=the_class, current_section=section)
        print('pdf_name = %s' % pdf_name)

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
        report_card_top = session_top
        stu_detail_top = report_card_top - 20
        tab = 50
        c.setFont(font, 14)

        try:
            ms = Marksheet.objects.get(school=school)
            title_start = ms.title_start
            address_start = ms.address_start
            affiliation = ms.affiliation
        except Exception as e:
            print('failed to retrieve the start coordinates for school name and address %s ' % school.school_name)
            print('exception 07022019-A from exam view.py %s %s' % (e.message, type(e)))
            title_start = 130
            address_start = 155
        left_margin = -30
        stu_name_lbl = 'Student Name:'
        class_sec_lbl = 'Class/Section:'

        exams = Exam.objects.filter(school=school, exam_type='term')
        for s in students:
            c.translate(inch, inch)
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
            report_card = 'Performance Analysis Sheet'
            c.drawString(152, report_card_top, report_card)

            c.setFont(font, 10)
            c.drawString(left_margin, stu_detail_top, stu_name_lbl)
            c.drawString(tab, stu_detail_top, '%s' % s )
            c.drawString(tab + 140, stu_detail_top, 'Adm No: ')
            c.drawString(tab + 190, stu_detail_top, s.student_erp_id)
            c.drawString(tab + 270, stu_detail_top, class_sec_lbl)
            # c.drawString(left_margin, stu_detail_top - 60, class_sec_lbl)
            c.drawString(tab + 350, stu_detail_top, standard + '-' + sec)

            c.setFont(font, 6)
            dy = inch * 3 / 4.0
            w = h = dy / 6
            c.setFillColorRGB(1, 0, 0)
            c.rect(tab, stu_detail_top - 40, w, h, fill=1)
            c.drawString(tab + 10, stu_detail_top - 37, 'Red (First) Column: Your Marks')

            c.setFillColorRGB(0, 1, 0)
            c.rect(tab + 100, stu_detail_top - 40, w, h, fill=1)
            c.drawString(tab + 110, stu_detail_top - 37, 'Green (Second) Column: Highest Marks')

            c.setFillColorRGB(0, 0, 1)
            c.rect(tab + 220, stu_detail_top - 40, w, h, fill=1)
            c.drawString(tab + 230, stu_detail_top - 37, 'Blue (Third) Column: Average Marks')

            c.setFillColor(black)

            analytics_top = stu_detail_top - 60
            for exam in exams:
                title = exam.title
                subject_analysis = SubjectAnalysis.objects.filter(student=s, exam=exam)
                if subject_analysis.count() > 0:
                    subject_count = subject_analysis.count()
                    print('generating analytics for %s of %s-%s' % (s, s.current_class,
                                                                    s.current_section))
                    c.drawString(left_margin, analytics_top, title)
                    c.drawString(left_margin, analytics_top - 10, 'Subject-wise comparative Analysis')

                    marks_array = []
                    subject_array = []
                    highest_array = []
                    average_array = []

                    for a_subject in subject_analysis:
                        subject = a_subject.subject.subject_name
                        subject_array.append(subject)

                        marks = a_subject.total_marks
                        marks_array.append(float(marks))

                        highest = a_subject.highest
                        highest_array.append(float(highest))

                        average = a_subject.average
                        average_array.append(float(average))
                    subject_wise = Drawing(400, 200)
                    data = [marks_array, highest_array, average_array]
                    bc = VerticalBarChart()
                    bc.x = 50
                    bc.y = 50
                    bc.height = 200
                    bc.width = 300
                    bc.barSpacing = 1.5
                    bc.strokeColor = colors.black
                    bc.valueAxis.valueMin = 0
                    bc.valueAxis.valueMax = 105
                    bc.valueAxis.valueStep = 10
                    bc.categoryAxis.labels.boxAnchor = 'ne'
                    bc.categoryAxis.labels.dx = -5
                    bc.categoryAxis.labels.dy = -2
                    bc.categoryAxis.labels.angle = 30
                    bc.barLabels.fontName = "Helvetica"
                    bc.barLabels.fontSize = 4
                    bc.barLabels.fontSize = 6
                    bc.barLabels.fillColor = black
                    bc.barLabelFormat = '%d'
                    bc.barLabels.nudge = 7
                    bc.data = data
                    bc.categoryAxis.categoryNames = subject_array
                    subject_wise.add(bc)
                    subject_wise.drawOn(c, left_margin -50, analytics_top - 270)

                    c.drawString(left_margin + 350, analytics_top - 10,
                                 'Comparison of Total Marks with Class Highest/Average')
                    total_wise = ExamHighestAverage.objects.get(exam=exam, the_class=the_class, section=section)
                    class_highest = float(total_wise.highest)
                    class_average = float(total_wise.average)
                    student_total = StudentTotalMarks.objects.get(exam=exam, student=s)
                    total_marks = float(student_total.total_marks)
                    data = [(total_marks,), (class_highest,), (class_average,)]
                    class_total = Drawing(100, 100)
                    bc.valueAxis.valueMax = subject_count * 100 + 40
                    bc.valueAxis.valueStep = 100
                    bc.width = 100
                    bc.data = data
                    bc.categoryAxis.categoryNames = None
                    class_total.add(bc)
                    class_total.drawOn(c, left_margin + 300, analytics_top - 270)

                    c.setFont(font, 12)
                    c.drawString(left_margin + 465, analytics_top - 60, "Percentage")
                    percentage = StudentTotalMarks.objects.get(student=s, exam=exam).percentage
                    d = Drawing(300, 200)
                    lab = Label()
                    lab.setOrigin(50,90)
                    lab.boxAnchor = 'ne'
                    lab.angle = 0
                    lab.dx = 5
                    lab.dy = 5
                    lab.width = 40
                    lab.height = 15
                    lab.textAnchor = 'middle'
                    lab.fontSize = 10
                    lab.boxStrokeColor = colors.green
                    lab.setText('%s%%' % str(percentage))
                    d.add(lab)
                    d.drawOn(c, left_margin + 457, analytics_top - 160)
                    c.drawString(left_margin + 478, analytics_top - 120, "Rank")
                    c.line(left_margin + 478, analytics_top - 137, left_margin + 505, analytics_top - 137)
                    rank = str(StudentTotalMarks.objects.get(student=s, exam=exam).rank)
                    out_of = str(StudentTotalMarks.objects.get(student=s, exam=exam).out_of)
                    if len(rank) > 1:
                        c.drawString(left_margin + 486, analytics_top - 135, str(rank))
                    else:
                        c.drawString(left_margin + 489, analytics_top - 135, str(rank))
                    c.drawString(left_margin + 486, analytics_top - 148, str(out_of))

                    analytics_top -= 300
            c.showPage()
        try:
            c.save()
            return response
        except Exception as e:
            print('exception 29102019-A from analytics views.py %s %s' % (e.message, type(e)))
            print('error in saving the pdf')
            return HttpResponse


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
