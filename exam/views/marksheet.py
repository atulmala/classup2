from PIL import Image
from decimal import Decimal

from google.cloud import storage

from django.http import HttpResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

from analytics.models import SubjectAnalysis
from attendance.models import IndividualAttendance
from exam.models import Marksheet, ExamResult
from exam.views import get_wings, HigherClassMapping, Scheme, get_grade
from setup.models import School, Configurations
from academics.models import Class, Section, Exam, Subject, ClassTest, TestResults, TermTestResult, CoScholastics, \
    ThirdLang
from student.models import Student, AdditionalDetails, DOB


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class GenerateMarksheet(generics.ListAPIView):
    school_logo = None

    def get(self, request, *args, **kwargs):
        print('at least entered get')
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        school_name = school.school_name
        school_address = school.school_address
        print(school)
        the_class = self.kwargs['the_class']
        standard = Class.objects.get(school=school, standard=the_class)
        print(standard)
        section = self.kwargs['section']
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
            affiliation_start = ms.affiliation_start
            board_logo_path = ms.board_logo_path
            print('board_logo_path = %s' % board_logo_path)
        except Exception as e:
            print('failed to retrieve the start coordinates for school name and address %s ' % school.school_name)
            print('exception 03012020-A from exam marksheet.py %s %s' % (e.message, type(e)))
            title_start = 130
            address_start = 155

        # 04/01/2018 get the logos
        try:
            conf = Configurations.objects.get(school=school)
            short_name = conf.school_short_name
        except Exception as e:
            print('failed to retrieve the short name for %s' % school_name)
            print('exception 03012020-A2 from exam marksheet.py %s %s' % (e.message, type(e)))

        wings = get_wings(school)
        junior_classes = wings['junior_classes']
        middle_classes = wings['middle_classes']
        ninth_tenth = wings['ninth_tenth']
        higher_classes = wings['higher_classes']

        whole_class = request.GET.get('whole_class')
        print(whole_class)
        selected_student = request.GET.get('selected_student')
        print (selected_student)

        if whole_class == 'true':
            pdf_name = '%s-%s%s' % (the_class, section, '_Term2_Results.pdf')

            # get the list of all the students, then get the marks of each test conducted for this exam
            students = Student.objects.filter(school=school, current_class=standard,
                                              current_section=sec, active_status=True)
        else:
            adm_no = selected_student.partition('(')[-1].rpartition(')')[0]
            print('admission/registrtion no is %s' % adm_no)
            students = Student.objects.filter(school=school, student_erp_id=adm_no)
            print(students)
            selected_student = ('%s_%s' % (students[0].fist_name, students[0].last_name))
            print('selected_student now = %s' % selected_student)
            pdf_name = ('%s_TermI_Results.pdf' % (selected_student))
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
            blob = bucket.blob(board_logo_path)
            blob.download_to_filename('exam/board_logo.png')
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
            print('exception 04022018-B from exam marksheet.py %s %s' % (e.message, type(e)))

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
            style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                      ('BOX', (0, 0), (-1, -1), 1, colors.black),
                      ('TOPPADDING', (0, 0), (-1, -1), 1),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                      ('ALIGN', (1, 0), (7, 0), 'CENTER'),
                      ('ALIGN', (8, 0), (14, 0), 'CENTER'),
                      ('SPAN', (1, 0), (7, 0)),
                      ('SPAN', (8, 0), (14, 0)),
                      ('FONTSIZE', (0, 0), (-1, -1), 7),
                      ('FONT', (0, 0), (13, 0), 'Times-Bold'),
                      ('FONT', (0, 1), (0, 1), 'Times-Bold')]

            # 29/09/2019 - comment when generating results for fianl exam
            # style1 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            #           ('BOX', (0, 0), (-1, -1), 1, colors.black),
            #           ('TOPPADDING', (0, 0), (-1, -1), 1),
            #           ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            #           ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            #           ('ALIGN', (1, 0), (7, 0), 'CENTER'),
            #           ('SPAN', (1, 0), (7, 0)),
            #
            #           ('FONTSIZE', (0, 0), (-1, -1), 7),
            #           ('FONT', (0, 0), (7, 0), 'Times-Bold'),
            #           ('FONT', (0, 1), (0, 1), 'Times-Bold')]
            # 29/09/2019  - uncomment when generating result for final exam
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

        if the_class in middle_classes:
            data4 = [['MARKS RANGE', 'GRADE'],
                     ['91 - 100', 'A 1'],
                     ['81 - 90', 'A 2'],
                     ['71 - 80', 'B 1'],
                     ['61 - 70', 'B 2'],
                     ['51 - 60', 'C 1'],
                     ['41 - 50', 'C 2'],
                     ['33 - 40', 'D'],
                     ['32 & Below', 'E (Needs improvement)']]
        else:
            data4 = [['MARKS RANGE', 'GRADE'],
                     ['91 - 100', 'A 1'],
                     ['81 - 90', 'A 2'],
                     ['71 - 80', 'B 1'],
                     ['61 - 70', 'B 2'],
                     ['51 - 60', 'C 1'],
                     ['41 - 50', 'C 2'],
                     ['33 - 40', 'D'],
                     ['32 & Below', 'E(Fail)']]

        session = 'Academic Session 2019-20'
        adm_no_lbl = 'Admission No:'
        stu_name_lbl = 'Student Name:'
        father_name_lbl = 'Mother/Father Name:'
        dob_lbl = 'Date of Birth:'
        class_sec_lbl = 'Class/Section:'

        sub_dict = {}

        left_margin = -30

        for s in students:
            print('Entering loop')
            c.translate(inch, inch)
            c.drawInlineImage(school_logo, logo_left, 690, width=logo_width, height=50)
            c.drawInlineImage(board_logo, left_margin, 690, width=60, height=50)
            font = 'Times-Bold'
            c.setFont(font, 14)

            c.drawString(title_start, top + 20, school_name)
            c.setFont(font, 10)
            c.drawString(address_start, top + 7, school_address)
            c.setFont(font, 8)
            c.drawString(affiliation_start, top - 4, '(%s)' % affiliation)
            c.setFont(font, 10)
            c.line(-30, line_top, 6.75 * inch, line_top)

            c.setFont(font, 10)
            c.drawString(152, session_top + 2, session)
            print('heading created')

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
                print('exception 03012020-C from exam marksheet.py %s %s' % (e.message, type(e)))
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

            c.setFont(font, 8)
            if the_class in higher_classes:
                print('result being prepared for class %s. This will be in school own format' % the_class)

                data1 = [['', 'TERM RESULT', '', '', '', '', '', '', '', 'CUMULATIVE RESULT', '', '', ''],
                         ['\nSUBJECT', 'UT-I', 'UT-II', 'Half Yearly\nExam', '', '',
                          'Final Exam', '', '', 'Unit\nTest', 'Half Yearly\nExam', 'Final\nExam', 'Total'],
                         ['', '30', '80/70/30', 'Th', 'Pr/IA', 'Tot', 'Th', 'Pr/IA', 'Tot', '25', '25', '50', '100']]
                print('class %s is a higher class. Subject list will come from the student/subject mapping' %
                      the_class)
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
                    print('exception 03012020-D from exam marksheet.py %s %s' % (e.message, type(e)))

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
                                    if marks < -1000.0:
                                        marks = 'TBE'
                                    else:
                                        marks = 'ABS'
                                else:
                                    if float(test.max_marks) != 25.0:
                                        print('max marks for %s in %s were %f. Conversion is required' %
                                              (sub, a_unit_exam.title, float(test.max_marks)))
                                        out_of_25 = round((25 * marks) / float(test.max_marks), 2)

                                        ut_total = ut_total + out_of_25
                                sub_row.append(marks)
                            except Exception as e:
                                print('exception 03012020-E from exam marksheet.py %s %s' % (e.message, type(e)))
                                print('unit test for %s not created for %s' % (a_unit_exam, subject))
                        index = 0
                        for a_term_exam in term_exams:
                            try:
                                analysis = SubjectAnalysis.objects.get(student=s, exam=a_term_exam, subject=subject)
                                marks = float(analysis.marks)
                                if marks < 0.0:
                                    if marks < -1000.0:
                                        marks = 'TBE'
                                    else:
                                        marks = 'ABS'

                                prac_marks = float(analysis.prac_marks)
                                if prac_marks < 0.0:
                                    prac_marks = ' '
                                    tot_marks = marks
                                else:
                                    # 26032018 - there is a possibility that student was absent
                                    # in theory but present in practical
                                    if marks != 'ABS':
                                        tot_marks = marks + prac_marks
                                    else:
                                        tot_marks = prac_marks

                                sub_row.append(marks)
                                sub_row.append(prac_marks)
                                sub_row.append(tot_marks)

                                if index == 0:  # we are dealing with half-yearly exam
                                    print('dealing with half yearly exam')
                                    half_yearly_marks = marks
                                    print('half yearly marks =')
                                    print(half_yearly_marks)
                                if index == 1:  # we are dealing with final exam
                                    print('dealing with final exam')
                                    final_marks = marks
                                    print('final marks = ')
                                    print(final_marks)
                            except Exception as e:
                                print('exception 03012020-F from exam marksheet.py %s %s' % (e.message, type(e)))
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

                            if half_yearly_marks != 'ABS':
                                half_year_cumul = round((half_yearly_marks * float(25)) / float(subject.theory_marks),
                                                        2)
                                grand_total += half_year_cumul
                            else:
                                half_year_cumul = 'ABS'
                            sub_row.append(half_year_cumul)

                            if final_marks != 'ABS':
                                final_cumul = round(final_marks * float(50) / float(subject.theory_marks), 2)
                                grand_total += final_cumul
                            else:
                                final_cumul = 'ABS'

                            # 29/09/2019 - uncomment while generating result for final exam
                            sub_row.append(final_cumul)
                            grand_total = ut_cumul + half_year_cumul + final_cumul
                            sub_row.append(grand_total)
                        except Exception as e:
                            print(
                                'failed to enter Cumulative Result. This may be because certain marks not entered')
                            print('exception 03012020-G from exam marksheet.py %s %s' % (e.message, type(e)))
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
                    print ('Exception 03012020-H from exam marksheet.py %s %s' % (e.message, type(e)))

                # get the CoScholastic Grades for this student
                print('getting the Coscholastic grades for %s %s' % (s.fist_name, s.last_name))
                table2_top = table1_top - 100
                try:
                    data2 = [['Co-Scholastic Areas [On a 3-point(A-C) grading scale]', '']]
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
                        art_ed = co_scl.discipline
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
                        print('exception 03012020-X from exam marksheet.py %s %s' % (e.message, type(e)))
                except Exception as e:
                    print('failed to retrieve Co-scholastic grades for %s %s for ' % (s.fist_name, s.last_name))
                    print('exception 03012020-Z from exam marksheet.py %s %s' % (e.message, type(e)))

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
                    print('exception 03012020-Y from exam marksheet.py %s %s' % (e.message, type(e)))

                print('preparing table3 for %s %s' % (s.fist_name, s.last_name))
                table3_top = table2_top - 40
                try:
                    data3 = [['Grade', '']]
                    data3.append(dscpln_array)
                    table3 = Table(data3)
                    table3.setStyle(TableStyle(style3))
                    table3.wrapOn(c, 0, 0)
                    # table3.drawOn(c, left_margin, table3_top)
                    print('drawn table3 for %s %s' % (s.fist_name, s.last_name))
                except Exception as e:
                    print('failed to draw table3 for %s %s' % (s.fist_name, s.last_name))
                    print('exception 03012020-I from exam marksheet.py %s %s' % (e.message, type(e)))
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
                    print('exception 10022018-A from exam marksheet.py %s %s' % (e.message, type(e)))
                if the_class in middle_classes:
                    print('%s is in middle classes' % the_class)
                    end_class = 'VIII'
                    # 29/09/2019 - uncomment when generting final exam result
                    data1 = [['Scholastic\nAreas', 'Term-1 (100 Marks)', '', '', '', '', '', '',
                              'Term-2 (100 Marks)', '', '', '', '', '', ''],
                             ['Sub Name', 'Per\n Test\n(5)', 'Mult\nAssess\n(5)', 'Portfolio\n(5)', 'Sub\nEnrich\n(5)',
                              'Half\nYearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade',
                              'Per\n Test\n(5)', 'Mult\nAssess\n(5)', 'Portfolio\n(5)', 'Sub\nEnrich\n(5)',
                              'Yearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade']]

                    # 29/09/2019 - comment when generating final exam result
                    # data1 = [['Scholastic\nAreas', 'Term-1 (100 Marks)', '', '', '', '', '', ''],
                    #          ['Sub Name', 'Per\n Test\n(5)', 'Mult\nAssess\n(5)', 'Portfolio\n(5)',
                    #           'Sub\nEnrich\n(5)',
                    #           'Half\nYearly\nExam\n(80)', 'Marks\nObtained\n(100)', 'Grade']]
                if the_class in ninth_tenth:
                    end_class = 'X'
                    data1 = [['Scholastic\nAreas', 'Academic Year (100 Marks)', '', '', '', '', '', ''],
                             ['Sub Name', 'Per Test\n(5)', 'Multi\nAssess\n(5)',
                              'Portfolio\n(5)', 'Sub\nEnrich\n(5)',
                              'Yearly Exam\n(80)', 'Marks\nObtained\n(100)', 'Grade']]
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
                            print (
                                    'failed to determine third lang for %s. Exception 061117-B from exam views.py %s %s'
                                    % (s.fist_name, e.message, type(e)))
                    sub_row = [sub.subject_name]
                    terms = Exam.objects.filter(school=school, exam_type='term', end_class=end_class)
                    try:
                        for idx, term in enumerate(terms):
                            print(term)
                            # for class IX, only the result of Term2, ie the final exam is to be shown
                            print('idx = %d' % idx)
                            if idx == 0 and the_class in ninth_tenth:
                                continue

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
                                    total = float(main) + float(pa) + float(multi_assess) + float(
                                        notebook) + float(
                                        sub_enrich)
                                    print(total)

                                    if the_class in ninth_tenth:
                                        if sub.subject_name == 'Computer':
                                            print('suject is Computer and class is IX')
                                            pa = 'NA'
                                            multi_assess = 'NA'
                                            sub_enrich = 'NA'
                                            # main = tr.marks_obtained
                                            notebook = 'NA'
                                            ttr = TermTestResult.objects.get(test_result=tr)
                                            theory = tr.marks_obtained
                                            prac = ttr.prac_marks
                                            total = float(theory) + float(prac)
                                            main = 'Th: %.0f Pr: %.0f' % (float(theory), float(prac))
                                            print('main = %s' % main)

                                    # in case the student was absent we need to show ABS in the marksheet.
                                    if the_class not in higher_classes:
                                        try:
                                            if float(main) < 0.0:
                                                main = 'ABS'
                                                total = float(pa) + float(multi_assess) + float(notebook) + float(
                                                    sub_enrich)
                                        except Exception as e:
                                            print('exception 08032020-A from exam marksheet.py %s %s' %
                                                  (e.message, type(e)))
                                            print('looks like we were dealing with main of Computer in class IX')

                                        grade = get_grade(total)
                                        print('grade obtained by %s in %s exam of %s: %s' %
                                              (s.fist_name, term, sub.subject_name, grade))

                                    # grade = get_grade(total)
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
                                print('exception 03012020-A1 from exam marksheet.py %s %s' % (e.message, type(e)))
                        data1.append(sub_row)
                        print('sub_row = ')
                        print(sub_row)
                        print('data1 =')
                        print(data1)
                    except Exception as e:
                        print('Error while preparing results for %s in exam %s' % (sub, term))
                        print ('Exception 03012020-J from exam marksheet.py %s %s' % (e.message, type(e)))
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
                    print('Exception 03012020-K from exam marksheet.py %s %s' % (e.message, type(e)))

                # get the CoScholastic Grades for this student
                print('getting the Coscholastic grades for %s %s' % (s.fist_name, s.last_name))
                table2_top = table1_top - 70
                try:
                    if the_class in middle_classes:
                        # 29/09/2019- uncomment when generating result for final exam
                        data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale]', '',
                                  'Co-Scholastic Areas: Term-2[On a 3-point(A-C) grading scale]', '']]

                        # 29/09/2019 - comment while generating result for final exam
                        # data2 = [['Co-Scholastic Areas: Term-1[On a 3-point(A-C) grading scale]', '']]
                    if the_class in ninth_tenth:
                        data2 = [['Co-Scholastic Areas: Academic Year[On a 3-point(A-C) grading scale]', '']]
                    work_array = []
                    art_array = []
                    health_array = []
                    dscpln_array = []

                    # 29/09/2019 - uncomment while generating result for final exam
                    terms = ['term1', 'term2']

                    # 29/09/2019 - comment while generating result for final exam
                    # terms = ['term1']
                    if the_class in ninth_tenth:
                        # 29/09/2019 - uncomment while generating result for final exam
                        terms = ['term2']
                        # 29/09/2019 - comment while generating result for final exam
                        # terms = ['term1']

                    for term in terms:
                        # for class IX, only the result of Term2, ie the final exam is to be shown
                        if term == 'term1' and the_class in ninth_tenth:
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
                            print('exception 03012020-L from exam views.py %s %s' % (e.message, type(e)))
                except Exception as e:
                    print('failed to retrieve Co-scholastic grades for %s %s for ' % (s.fist_name, s.last_name))
                    print('exception 03012020-M from exam marksheet.py %s %s' % (e.message, type(e)))
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
                    print('exception 03012020-N from exam marksheet.py %s %s' % (e.message, type(e)))
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
                    print('exception 03012020-O from exam marksheet.py %s %s' % (e.message, type(e)))

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
                            print('exception 03012020-P from exam marksheet.py %s %s' % (e.message, type(e)))
                            print('attendance recored not available for %s' % s)

                    c.drawString(left_margin, table3_top - 55, 'Place & Date:')
                    # c.drawString(left_margin + 50, table3_top - 55, 'Noida   26/03/2018')
                    c.drawString(175, table3_top - 55, 'Signature of Class Teacher')
                    c.drawString(400, table3_top - 55, 'Signature of Principal')
                except Exception as e:
                    print('exception 03012020-Q from exam marksheet.py %s %s' % (e.message, type(e)))

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
                        c.drawString(left_margin + 50, table3_top - 25, '%s/%s' % (str(present_days), str(total_days)))
                    except Exception as e:
                        print('exception 03012020-R from exam marksheet.py %s %s' % (e.message, type(e)))
                        print('attendance recored not available for %s' % s)
                if the_class in ninth_tenth:
                    c.drawString(left_margin, table3_top - 35, 'Promoted to Class: ')
                else:
                    c.drawString(left_margin, table3_top - 35, 'Promoted to Class: ')
                try:
                    exam_result = ExamResult.objects.get(student=s)
                    if exam_result.status:
                        current_class = Class.objects.get(school=school, standard=the_class)
                        next_class_sequence = current_class.sequence + 1
                        next_class = Class.objects.get(school=school, sequence=next_class_sequence)
                        next_class_standard = next_class.standard
                        promoted_to = next_class_standard
                    else:
                        detain_reason = exam_result.detain_reason
                        promoted_to = 'Not Promoted. %s' % detain_reason
                    c.drawString(tab - 20, table3_top - 35, promoted_to)
                except Exception as e:
                    print('exception 26022020-A from exam marksheet.py %s %s' % (e.message, type(e)))
                    print('could not retrieve promotion status for %s' % s)

                c.drawString(tab - 20, table3_top - 25, '')
                c.drawString(left_margin, table3_top - 55, 'Place & Date:')
                place_date = '%s   %s' % (place, result_date)
                c.drawString(left_margin + 50, table3_top - 55, place_date)
                c.drawString(175, table3_top - 55, 'Signature of Class Teacher')
                c.drawString(400, table3_top - 55, 'Signature of Principal')
            except Exception as e:
                print('exception 03012020-S from exam marksheet.py %s %s' % (e.message, type(e)))

            if not ms.two_page:
                c.drawString(170, table3_top - 90, "Instructions")
                c.drawString(0, table3_top - 100, "Grading Scale for Scholastic Areas: "
                                                  "Grades are awarded on a 8-point grading scales as follows - ")
                table4 = Table(data4)
                table4.setStyle(TableStyle(style4))
                table4.wrapOn(c, 0, 0)
                table4.drawOn(c, 140, table3_top - 250)
            else:
                if the_class not in higher_classes:
                    c.drawString(170, -50, "Grading scheme on reverse")
                else:
                    c.drawString(170, -30, "Grading scheme on reverse")
                    c.drawString(110, -40, "Cumulative Results Calculations based on Theory marks only")
                    split = 'Theory/Prac Split - English, Mathematics, Accountancy, B.St, Economics: (80/20). '
                    split += 'Physics, Chemistry, Biology, Phy Ed, Comp Sc, IP: (70/30). '
                    split += 'Painting/Fine Arts (30/70)'
                    c.setFont(font, 6)
                    c.drawString(0, -50, split)
                c.showPage()
                c.drawString(260, 570, "Instructions")
                c.drawString(30, 550, "Grading Scale for Scholastic Areas: "
                                      "Grades are awarded on a 8-point grading scales as follows - ")
                table4 = Table(data4)
                table4.setStyle(TableStyle(style4))
                table4.wrapOn(c, 0, 0)
                table4.drawOn(c, 230, 400)
            c.showPage()

        try:
            c.save()
        except Exception as e:
            print('error in saving the pdf')
            print ('Exception 03012020-T from exam marksheet.py %s %s' % (e.message, type(e)))
        print('about to send the response')

        # 31/10/2018 - delete the downloaded png files for school and cbse logo
        try:
            import os
            os.remove('exam/board_logo.png')
            print('successfully removed cbse_logo.png')
            os.remove('exam/%s.png' % short_name)
            print('successfully removed %s.png' % short_name)
        except Exception as e:
            print('exception 01012020-U from exam marksheet.py %s %s' % (e.message, type(e)))
            print('failed to delete downloaded png files for cbse and school logo')
        return response
