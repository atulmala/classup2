import StringIO

import xlsxwriter
from google.cloud import storage

from django.http import HttpResponse

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from formats.formats import Formats as format

from setup.models import School
from student.models import Student
from academics.models import Class, Section, Subject, Exam
from analytics.models import StudentTotalMarks, SubjectAnalysis

from exam.views import get_wings


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class MasterData(generics.ListAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        school_id = request.query_params.get('school_id')
        school = School.objects.get(id=school_id)
        standard = request.query_params.get('standard')
        the_class = Class.objects.get(school=school, standard=standard)

        excel_file_name = '%s_%s_master_data.xlsx' % (str(school_id), the_class)

        print('excel_file_name = %s' % excel_file_name)

        output = StringIO.StringIO(excel_file_name)

        workbook = xlsxwriter.Workbook(output)
        fmt = format()
        cell_bold = workbook.add_format(fmt.get_cell_bold())
        cell_bold.set_border()
        cell_normal = workbook.add_format(fmt.get_cell_normal())
        cell_normal.set_border()
        cell_left = workbook.add_format(fmt.get_cell_left())
        cell_left.set_border()

        t1_sheet = workbook.add_worksheet('Term I')
        t2_sheet = workbook.add_worksheet('Term II')
        cons_sheet = workbook.add_worksheet('Consolidated')

        t1_sheet.set_column('B:B', 20)
        t2_sheet.set_column('B:B', 20)
        cons_sheet.set_column('B:B', 20)

        wings = get_wings(school)
        middle_classes = wings['middle_classes']
        ninth_tenth = wings['ninth_tenth']
        higher_classes = wings['higher_classes']

        if standard not in higher_classes:
            subject_list = ['English', 'Hindi', 'Sanskrit', 'French',
                            'Mathematics', 'Science', 'Social Studies', 'Computer']

            # prepare excel headers
            row = 0
            col = 0
            t1_sheet.write_string(row, col, 'S No', cell_bold)
            t2_sheet.write_string(row, col, 'S No', cell_bold)
            cons_sheet.write_string(row, col, 'S No', cell_bold)
            col += 1
            t1_sheet.write_string(row, col, 'Student', cell_bold)
            col += 1
            t1_sheet.write_string(row, col, 'Class', cell_bold)
            t2_sheet.write_string(row, col, 'Class', cell_bold)
            cons_sheet.write_string(row, col, 'Class', cell_bold)
            col += 1
            t1_sheet.write_string(row, col, 'Section', cell_bold)
            t2_sheet.write_string(row, col, 'Section', cell_bold)
            cons_sheet.write_string(row, col, 'Section', cell_bold)
            col += 1

            for subject in subject_list:
                t1_sheet.write_string(row, col, subject, cell_bold)
                t2_sheet.write_string(row, col, subject, cell_bold)
                cons_sheet.write_string(row, col, subject, cell_bold)
                col += 1
            t1_sheet.write_string(row, col, 'Total', cell_bold)
            t2_sheet.write_string(row, col, 'Total', cell_bold)
            cons_sheet.write_string(row, col, 'Total', cell_bold)

            row += 1
            col = 0
            s_no = 1
            students = Student.objects.filter(current_class=the_class).order_by('fist_name').order_by('current_section')
            for student in students:
                print('extracting marks in each subject for %s of %s-%s' %
                      (student, student.current_class, student.current_section))

                t1_sheet.write_number(row, col, s_no, cell_normal)
                t2_sheet.write_number(row, col, s_no, cell_normal)
                cons_sheet.write_number(row, col, s_no, cell_normal)
                s_no += 1
                col += 1

                student_name = '%s %s' % (student.fist_name, student.last_name)
                t1_sheet.write_string(row, col, student_name, cell_left)
                t2_sheet.write_string(row, col, student_name, cell_left)
                cons_sheet.write_string(row, col, student_name, cell_left)
                col += 1

                t1_sheet.write_string(row, col, student.current_class.standard, cell_normal)
                t2_sheet.write_string(row, col, student.current_class.standard, cell_normal)
                cons_sheet.write_string(row, col, student.current_class.standard, cell_normal)
                col += 1

                t1_sheet.write_string(row, col, student.current_section.section, cell_normal)
                t2_sheet.write_string(row, col, student.current_section.section, cell_normal)
                cons_sheet.write_string(row, col, student.current_section.section, cell_normal)
                col += 1

                exams = Exam.objects.filter(exam_type='term', end_class='VIII')
                for a_subject in subject_list:
                    subject = Subject.objects.get(school=school, subject_name=a_subject)
                    subject_total = 0.0
                    try:
                        analysis1 = SubjectAnalysis.objects.get(student=student, exam=exams[0], subject=subject)
                        marks = analysis1.total_marks
                        subject_total += float(marks)
                        t1_sheet.write_number(row, col, marks, cell_normal)
                    except Exception as e:
                        print('exception 07012020-A from analytics master_data.py %s %s' % (e.message, type(e)))
                        print('cound not retrieve subject marks for %s subject %s in %s exam for %s of %s-%s' %
                              (student, subject, exams[0], student, the_class, student.current_section))

                    try:
                        analysis2 = SubjectAnalysis.objects.get(student=student, exam=exams[1], subject=subject)
                        marks = analysis2.total_marks
                        subject_total += float(marks)
                        t2_sheet.write_number(row, col, marks, cell_normal)
                    except Exception as e:
                        print('exception 07012020-B from analytics master_data.py %s %s' % (e.message, type(e)))
                        print('cound not retrieve subject marks for %s subject %s in %s exam for %s of %s-%s' %
                              (student, subject, exams[0], student, the_class, student.current_section))

                    cons_sheet.write_number(row, col, subject_total, cell_normal)
                    col += 1

                try:
                    total_marks1 = StudentTotalMarks.objects.get(student=student, exam=exams[0]).total_marks
                    t1_sheet.write_number(row, col, total_marks1)
                except Exception as e:
                    print('exception 07012020-C from analytics master_data.py %s %s' % (e.message, type(e)))
                    print('cound not retrieve total marks for %s  in %s exam for %s of %s-%s' %
                          (student, exams[0], student, the_class, student.current_section))

                try:
                    total_marks2 = StudentTotalMarks.objects.get(student=student, exam=exams[1]).total_marks
                    t2_sheet.write_number(row, col, total_marks2)
                except Exception as e:
                    print('exception 07012020-D from analytics master_data.py %s %s' % (e.message, type(e)))
                    print('cound not retrieve total marks for %s  in %s exam for %s of %s-%s' %
                          (student, exams[1], student, the_class, student.current_section))

                row += 1
                col = 0
        workbook.close()

        # 17/01/2019 - upload file to cloud storage
        try:
            storage_client = storage.Client()
            bucket = storage_client.get_bucket('classup')
            file_path = 'classup2/Analytics/school/%s/%s' % (str(school_id), excel_file_name)
            blob = bucket.blob(file_path)
            blob.upload_from_string(output.getvalue())
            print('successfully uploaded %s master data file to cloud storage' % file_path)
        except Exception as e:
            print('exception 17012020-A from analytics master_data.py %s %s' % (e.message, type(e)))
            print('failed to upload %s to cloud storage' % file_path)

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response
