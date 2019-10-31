import ast
import statistics

from django.db.models import Sum, Avg, Count
from django.http import HttpResponse
from reportlab.lib.colors import black
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.graphics.shapes import Rect
from reportlab.graphics.charts.textlabels import Label
from reportlab.platypus import Table, TableStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart

from authentication.views import JSONResponse

from setup.models import School
from student.models import Student
from academics.models import Class, Section, Subject, Exam, ClassTest, TestResults, TermTestResult, ThirdLang
from exam.models import Wing, Scheme, Marksheet
from .models import SubjectAnalysis, SubjectHighestAverage, ExamHighestAverage, StudentTotalMarks


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

        try:
            jc = Wing.objects.get(school=school, wing='junior_classes')
            junior_classes = ast.literal_eval(jc.classes)
            print('junior_classes for %s are: ' % school)
            print(junior_classes)
        except Exception as e:
            print('exception 26102019-Z from analytics views.py %s %s' % (e.message, type(e)))
            print('junior_classes not defined for %s' % school)
            junior_classes = ['not defined']

        try:
            mc = Wing.objects.get(school=school, wing='middle_classes')
            print('raw middle_classes retrieved for %s: %s. Will be converted to proper string now' %
                  (school, mc.classes))
            middle_classes = ast.literal_eval(mc.classes)
            print('middle_classes for %s are: ' % school)
            print(middle_classes)
        except Exception as e:
            print('exception 26102019-Y from analytics views.py %s %s' % (e.message, type(e)))
            print('middle_classes not defined for %s' % school)
            middle_classes = ['not defined']

        try:
            nt = Wing.objects.get(school=school, wing='ninth_tenth')
            ninth_tenth = ast.literal_eval(nt.classes)
            print('ninth_tenth for %s are: ' % school)
            print(ninth_tenth)
        except Exception as e:
            print('exception 26102019-X from analytics.py %s %s' % (e.message, type(e)))
            print('ninth_tenth not defined for %s' % school)
            ninth_tenth = ['not defined']

        try:
            hc = Wing.objects.get(school=school, wing='higher_classes')
            higher_classes = ast.literal_eval(hc.classes)
            print('higher_classes for %s are: ' % school)
            print(higher_classes)
        except Exception as e:
            print('exception 26102019-W from analytics.py %s %s' % (e.message, type(e)))
            print('higher_classes not defined for %s' % school)
            higher_classes = ['not defined']
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
                        average = statistics.mean(marks_array)
                        highest = max(marks_array)

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
        context_dict = {

        }

        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        school_name = school.school_name
        school_address = school.school_address
        cl = self.kwargs['the_class']
        the_class = Class.objects.get(school=school, standard=cl)
        sec = self.kwargs['section']
        section = Section.objects.get(school=school, section=sec)

        whole_class = True
        selected_student = self.kwargs['selected_student']
        print('selected student = %s' % selected_student)
        if selected_student != 'na':
            whole_class = False
            adm_no = selected_student.partition('(')[-1].rpartition(')')[0]
            print('admission/registrtion no is %s' % adm_no)
            s = Student.objects.get(school=school, student_erp_id=adm_no)
            print(s)
            selected_student = ('%s_%s' % (s.fist_name, s.last_name))
            students = [selected_student]
            print('selected_student now = %s' % selected_student)
            pdf_name = ('%s_%s_Performance_Analyis.pdf' % (s.fist_name, s.last_name))

        if whole_class:
            pdf_name = '%s-%s%s' % (cl, sec, '_Performance_Analysis.pdf')
            students = Student.objects.filter(current_class=the_class, current_section=section)
        print('pdf_name = %s' % pdf_name)

        if request.method == 'GET':
            if whole_class:
                pdf_name = '%s-%s%s' % (the_class, section, '_Performance_Analysis.pdf')
                # pdf_name = the_class + '-' + section + '_Term1_Results.pdf'
            else:
                adm_no = selected_student.partition('(')[-1].rpartition(')')[0]
                print('admission/registrtion no is %s' % adm_no)
                s = Student.objects.get(school=school, student_erp_id=adm_no)
                print(s)
                selected_student = ('%s_%s' % (s.fist_name, s.last_name))
                print('selected_student now = %s' % selected_student)
                pdf_name = ('%s_%s_Performance_Analysis.pdf' % (s.fist_name, s.last_name))
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
        for student in students:
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
            c.drawString(tab, stu_detail_top, '%s' % student )
            c.drawString(tab + 140, stu_detail_top, 'Adm No: ')
            c.drawString(tab + 190, stu_detail_top, student.student_erp_id)
            c.drawString(tab + 270, stu_detail_top, class_sec_lbl)
            # c.drawString(left_margin, stu_detail_top - 60, class_sec_lbl)
            c.drawString(tab + 350, stu_detail_top, cl + '-' + sec)

            c.setFont(font, 6)
            dy = inch * 3 / 4.0
            dx = inch * 5.5 / 5
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
                subject_analysis = SubjectAnalysis.objects.filter(student=student, exam=exam)
                if subject_analysis.count() > 0:
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
                    student_total = StudentTotalMarks.objects.get(exam=exam, student=student)
                    total_marks = float(student_total.total_marks)
                    data = [(total_marks,), (class_highest,), (class_average,)]
                    class_total = Drawing(100, 100)
                    bc.valueAxis.valueMax = 740
                    bc.valueAxis.valueStep = 100
                    bc.width = 100
                    bc.data = data
                    bc.categoryAxis.categoryNames = None
                    class_total.add(bc)
                    class_total.drawOn(c, left_margin + 300, analytics_top - 270)

                    c.setFont(font, 12)
                    c.drawString(left_margin + 465, analytics_top - 60, "Percentage")
                    percentage = StudentTotalMarks.objects.get(student=student, exam=exam).percentage
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
                    rank = str(StudentTotalMarks.objects.get(student=student, exam=exam).rank)
                    out_of = str(StudentTotalMarks.objects.get(student=student, exam=exam).out_of)
                    if len(rank) > 1:
                        c.drawString(left_margin + 486, analytics_top - 135, str(rank))
                    else:
                        c.drawString(left_margin + 489, analytics_top - 135, str(rank))
                    c.drawString(left_margin + 486, analytics_top - 148, str(out_of))

            c.showPage()
        try:
            c.save()
            return response
        except Exception as e:
            print('exception 29102019-A from analytics views.py %s %s' % (e.message, type(e)))
            print('error in saving the pdf')
            return HttpResponse
