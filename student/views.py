
# Create your views here.

import StringIO
import xlsxwriter
import xlrd


from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Max

from setup.models import School
from academics.models import ClassTest, TestResults, TermTestResult, ThirdLang, Class, Section
from exam.models import HigherClassMapping, NPromoted
from exam.forms import ResultSheetForm
from .models import Student, Parent

from setup.forms import ExcelFileUploadForm
from .forms import MidTermAdmissionForm

from setup.views import validate_excel_extension

from .serializers import StudentSerializer, ParentSerializer

from authentication.views import JSONResponse

from operations import sms

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class StudentList(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        """
        :return: list of all students based on class and section supplied by the URL
        """
        print (self.request._request)
        print (self.kwargs)

        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        the_class = self.kwargs['the_class']
        section = self.kwargs['section']

        q1 = Student.objects.filter(school=school, current_section__section=section,
                                    current_class__standard=the_class, active_status=True)
        q2 = q1.order_by('fist_name')
        return q2


class StudentListForTest(generics.ListCreateAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        test_id = self.kwargs['test_id']

        query_set = ClassTest.objects.filter(pk=test_id)[:1]
        for q in query_set:
            the_class = q.the_class
            print ('class=')
            print (the_class)

            section = q.section
            print ('section=')
            print (section)

        q1 = Student.objects.filter(current_section__section=section,
                                    current_class__standard=the_class, active_status=True)
        q2 = q1.order_by('fist_name')
        return q2


class StudentListForParent(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        parent_mobile = self.kwargs['parent_mobile']

        the_parent = Parent.objects.get(parent_mobile1=parent_mobile)
        q1 = Student.objects.filter(parent=the_parent, active_status=True).order_by('fist_name')
        return q1


def get_parent(request, student_id):
    parent_detail = {

    }

    if request.method == 'GET':
        try:
            student = Student.objects.get(id=student_id)
            parent = student.parent
            parent_detail['parent_name'] = parent.parent_name
            parent_detail['parent_mobile1'] = parent.parent_mobile1
            parent_detail['parent_mobile2'] = parent.parent_mobile2
            parent_detail['status'] = 'ok'
        except Exception as e:
            print ('Exception1 from student views.py = %s (%s)' % (e.message, type(e)))
            print('unable to fetch parent name and mobile for student id: ' + student_id)
            parent_detail['status'] = 'error'
            return JSONResponse(parent_detail, status=201)

        return JSONResponse(parent_detail, status=201)


def get_student_detail(request, student_id):
    student_detail =    {

    }
    if request.method == 'GET':
        try:
            student = Student.objects.get(id=student_id)
            student_detail['erp_id'] = student.student_erp_id
            student_detail['first_name'] = student.fist_name
            student_detail['last_name'] = student.last_name
            student_detail['class'] = student.current_class.standard
            student_detail['section'] = student.current_section.section
            student_detail['roll_no'] = str(student.roll_number)
            student_detail['parent_name'] = student.parent.parent_name
            student_detail['parent_mobile1'] = str(student.parent.parent_mobile1)
            student_detail['parent_mobile2'] = str(student.parent.parent_mobile2)
        except Exception as e:
            print('Exception 10 from student views.py = %s (%s)' % (e.message, type(e)))
            print('unable to get student details with student id ' + student_id)
        return JSONResponse(student_detail)


class ParentList(generics.ListAPIView):
    serializer_class = ParentSerializer

    def get_queryset(self):
        print('inside queryset')
        student_id = self.kwargs['student_id']

        q = Parent.objects.filter(student__id=student_id)
        return q

class PromoteStudents(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Upload Student Promotion List'
        form = ExcelFileUploadForm()
        context_dict['form'] = form
        return render(request, 'classup/setup_data.html', context_dict)


class StudentListDownload (generics.ListAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Download Result Sheets'

        if request.session['user_type'] == 'school_admin':
            context_dict['user_type'] = 'school_admin'

        school_id = request.session['school_id']
        form = ResultSheetForm(school_id=school_id)
        context_dict['form'] = form
        return render(request, 'classup/student_list.html', context_dict)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Download Result Sheets'

        if request.session['user_type'] == 'school_admin':
            context_dict['user_type'] = 'school_admin'
        if "cancel" in request.POST:
            return render(request, 'classup/student_list.html', context_dict)
        else:
            school_id = request.session['school_id']
            school = School.objects.get(id=school_id)
            school_name = school.school_name
            school_name = school_name.replace(' ', '_')
            form = ResultSheetForm(request.POST, school_id=school_id)

            if form.is_valid():
                the_class = form.cleaned_data['the_class']
                section = form.cleaned_data['section']
                print ('result sheet will be generated for %s-%s' % (the_class.standard, section.section))

                excel_file_name = 'Student_List' + str(the_class.standard) + '-' + str(section.section) + '.xlsx'
                excel_file_name = '%s_Student_List_%s-%s.xlsx' % (str(school_name), str(the_class.standard), str(section.section))
                output = StringIO.StringIO(excel_file_name)
                workbook = xlsxwriter.Workbook(output)
                sheet = workbook.add_worksheet('Student List %s-%s' % (str(the_class.standard), section.section))

                border = workbook.add_format()
                border.set_border()

                title = workbook.add_format({
                    'bold': True,
                    'font_size': 14,
                    'align': 'center',
                    'valign': 'vcenter'
                })

                cell_normal = workbook.add_format({
                    'align': 'left',
                    'valign': 'top',
                    'text_wrap': True
                })
                cell_normal.set_border()
                cell_center = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'text_wrap': True,
                    'bold': True
                })
                cell_center.set_border()
                vertical_text = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'bold': True,
                    'rotation': 90
                })
                vertical_text.set_border()


                row = 0
                col = 0
                sheet.write_string (row, col, 'S No', title)
                col = col + 1
                sheet.set_column ('B:B', 16)
                sheet.write_string (row, col, 'Admission No', title)
                col = col + 1
                sheet.set_column ('C:G', 20)
                sheet.write_string (row, col, 'Student Name', title)

                # 06/03/2018 - coding to show the current class/sec and promoted class/sec will be required only during
                # new session start, otherwise will be coded
                col += 1
                sheet.write_string(row, col, 'Current Class', title)
                col += 1
                sheet.write_string(row, col, 'Current Section', title)
                col += 1
                sheet.write_string(row, col, 'Promoted Class', title)
                col += 1
                sheet.write_string(row, col, 'Promoted Section', title)

                try:
                    students = Student.objects.filter(school=school, current_class=the_class,
                                                      current_section=section, active_status=True).order_by('fist_name')
                    print ('retrieved the list of students for %s-%s' % (the_class.standard, section.section))
                    print (students)
                    row = row + 1
                    col = 0
                    s_no = 1
                    for student in students:
                        sheet.write_number (row, col, s_no, cell_normal)
                        col = col + 1
                        sheet.write_string (row, col, student.student_erp_id, cell_normal)
                        col = col + 1
                        student_name = '%s %s' % (student.fist_name, student.last_name)
                        sheet.write_string (row, col, student_name, cell_normal)

                        # current class & section
                        col += 1
                        current_class = student.current_class.standard
                        sheet.write_string (row, col, current_class, cell_normal)
                        col += 1
                        current_section = student.current_section.section
                        sheet.write_string(row, col, current_section, cell_normal)
                        col += 1

                        # promoted class & section
                        current_class_seq = student.current_class.sequence
                        next_class_seq = current_class_seq + 1
                        try:
                            next = Class.objects.get(school=student.school, sequence=next_class_seq)
                            next_class = next.standard
                            print('determined the next class for %s: %s-%s' %
                                  (student_name, next_class, current_section))
                            sheet.write_string(row, col, next_class, cell_normal)
                            col += 1
                            sheet.write_string(row, col, current_section, cell_normal)
                        except Exception as e:
                            print('failed to determine the next class for %s' % student_name)
                            print('exception 06032018-A from student views.py %s %s' % (e.message, type(e)))
                        row = row + 1
                        s_no = s_no + 1
                        col = 0
                    workbook.close()
                    response = HttpResponse(content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
                    response.write(output.getvalue())
                    return response

                except Exception as e:
                    print ('exception 21010218-A from student views.py %s %s' % (e.message, type(e)))
                    print ('failed to retrieve the list of students for %s-%s' % (the_class.standard, section.section))
                    workbook.close()
                    response = HttpResponse(content_type='application/vnd.ms-excel')
                    response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
                    response.write(output.getvalue())
                    return response
            else:
                error = 'You have missed to select either Class, or Section'
                form = ResultSheetForm(request)
                context_dict['form'] = form
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/result_sheet.html', context_dict)


class MidTermAdmission (generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Mid Term Admission (create entry in Tests for the New Admission)'

        if request.session['user_type'] == 'school_admin':
            context_dict['user_type'] = 'school_admin'

        school_id = request.session['school_id']
        form = MidTermAdmissionForm(school_id=school_id)
        context_dict['form'] = form
        return render(request, 'classup/mid_term_admission.html', context_dict)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Mid Term Admission (create entry in Tests for the New Admission)'

        if request.session['user_type'] == 'school_admin':
            context_dict['user_type'] = 'school_admin'
        if "cancel" in request.POST:
            return render(request, 'classup/mid_term_admission.html', context_dict)
        else:
            school_id = request.session['school_id']
            school = School.objects.get(id=school_id)
            form = MidTermAdmissionForm(request.POST, school_id=school_id)

            if form.is_valid():
                higher_classes = ['XI', 'XII']
                ninth_tenth = ['IX', 'X']
                middle_classes = ['V', 'VI', 'VII', 'VIII']
                junior_classes = ['Nursery', 'LKG', 'UKG', 'I', 'II', 'III', 'IV']

                admission_no = form.cleaned_data['admission_no']
                print('admission no = %s' % admission_no)

                # retrieve student associated with this admission number
                try:
                    student = Student.objects.get(school=school, student_erp_id=admission_no)
                    print(student)
                    student_name = student.fist_name + ' ' + student.last_name

                    # determine the class & section of this student
                    the_class = student.current_class
                    section = student.current_section

                    # get the list of all tests created for this class
                    tests = ClassTest.objects.filter (the_class=the_class, section=section)
                    print('total %i test results to be created for %s' % (tests.count(), student_name))
                    print(tests)
                    for test in tests:
                        subject = test.subject
                        # create the test result for this student ONLY if it is not already created!
                        try:
                            test_result = TestResults.objects.get(class_test=test, student=student)
                            print(test_result)
                            print('test = ')
                            print(test)
                            print('results for the above test are already created for %s. Hence doing nothing' %
                                  student_name)
                        except Exception as e:
                            print('exception 22010218-B from student views.py %s %s' % (e.message, type(e)))
                            print('test = ')
                            print(test)
                            print('results for the above test are not yet created for %s. Will create now' %
                                  student_name)
                            if subject.subject_type == 'Third Language':
                                print ('%s is a Third Language. Test results will be created only if %s has opted' %
                                       (subject.subject_name, student_name))
                                try:
                                    third_lang = ThirdLang.objects.get(third_lang=subject, student=student)
                                    print(third_lang)
                                    print ('%s has chosen %s as third language' % (student_name, subject.subject_name))
                                    test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                                              student=student, marks_obtained=-5000.00,grade='')
                                    try:
                                        test_result.save()
                                        print ('test results successfully created for subject %s for %s' %
                                               (subject.subject_name, student_name))

                                        # some more data need to be created for a Term test
                                        try:
                                            if test.test_type == 'term':
                                                term_test_result = TermTestResult(test_result=test_result,
                                                                                  periodic_test_marks=-5000.0,
                                                                                  note_book_marks=-5000.0,
                                                                                  sub_enrich_marks=-5000.0)
                                                term_test_result.save()
                                                print (' term test results successfully created for % s %s' %
                                                       (student.fist_name, student.last_name))
                                        except Exception as e:
                                            message = 'failed to create term test results for subject %s for %s' % \
                                                      (subject.subject_name, student_name)
                                            print (message)
                                            print ('Exception 22012018-C from student views.py = %s (%s)' %
                                                   (e.message, type(e)))
                                    except Exception as e:
                                        print ('failed to create test results')
                                        print ('Exception 22010218-E from student views.py = %s (%s)' %
                                               (e.message, type(e)))
                                        return HttpResponse('Failed to create test results')
                                except Exception as e:
                                    print ('Exception 22010218-D from student views.py %s %s' % (e.message, type(e)))
                                    print ('%s has not chosen %s as third language' % (
                                    student_name, subject.subject_name))
                            else:
                                print ('this is a regular subject. Mapping will be considered for higher class only')

                                # for higher classes (XI & XII) we need to look into the student subject mapping
                                if the_class.standard in higher_classes:
                                    print ('test is for higher class %s. Hence, mapping will be considered' %
                                           the_class.standard)
                                    try:
                                        mapping = HigherClassMapping.objects.get(student=student, subject=subject)
                                        if mapping:
                                            test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                                                      student=student, marks_obtained=-5000.00,
                                                                      grade='')
                                            test_result.save()
                                            print ('test results successfully created for subject %s for %s' % (
                                                subject.subject_name, student_name))

                                            # in case of higher class practical marks need to be initialized
                                            if test.test_type == 'term':
                                                term_test_result = TermTestResult(test_result=test_result,
                                                                                  prac_marks=-5000.0)
                                                term_test_result.save()
                                                print ('term test results successfully created for subject %s for %s' %
                                                       (subject.subject_name, student_name))
                                    except Exception as e:
                                        print ('mapping does not exist between subject %s and %s' %
                                               (subject.subject_name, student_name))
                                        print ('exception 22010218-F from student views.py %s %s' %
                                               (e.message, type(e)))

                                # for IX & X Hindi is also an elective subject. If subject is Hindi and class is
                                # IX or X, then test result will be created for selected students only
                                if the_class.standard in ninth_tenth:
                                    print('%s is in %s. Mapping will be checked only for Hindi' %
                                          (student_name, the_class.standard))
                                    if subject.subject_name == 'Hindi':
                                        print ('mapping will have to be checked as the class is %s and subject is Hindi'
                                               % the_class.standard)
                                        try:
                                            second_lang = ThirdLang.objects.get(third_lang=subject, student=student)
                                            print(second_lang)
                                            print ('%s has chosen %s as second language' %
                                                   (student_name, subject.subject_name))
                                            test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                                                      student=student, marks_obtained=-5000.00,
                                                                      grade='')
                                            try:
                                                test_result.save()
                                                print ('test results successfully created for subject %s  for %s' %
                                                       (subject.subject_name, student_name))

                                                # 21/09/2017 some more data need to be created for a Term test
                                                try:
                                                    if test.test_type == 'term':
                                                        term_test_result = TermTestResult(test_result=test_result,
                                                                                          periodic_test_marks=-5000.0,
                                                                                          note_book_marks=-5000.0,
                                                                                          sub_enrich_marks=-5000.0)
                                                        term_test_result.save()
                                                        print ('term test results successfully created for subject %s '
                                                               'for %s' % (subject.subject_name, student_name))
                                                except Exception as e:
                                                    print('failed to create term test results subject %s for %s'
                                                          % (subject.subject_name, student_name))
                                                    print ('Exception 23012018-A from student views.py = %s (%s)' % (
                                                        e.message, type(e)))
                                            except Exception as e:
                                                print ('failed to create test results')
                                                print ('Exception 23012018-B from student views.py = %s (%s)' %
                                                       (e.message, type(e)))
                                        except Exception as e:
                                            print ('Exception 23012018-C from student views.py %s %s' % (
                                            e.message, type(e)))
                                            print ('%s has not chosen %s as second language' %
                                                   (student_name, subject.subject_name))
                                    else:
                                        test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                                                  student=student, marks_obtained=-5000.00, grade='')
                                        try:
                                            test_result.save()
                                            if test.test_type == 'term':
                                                term_test_result = TermTestResult(test_result=test_result,
                                                                                  periodic_test_marks=-5000.0,
                                                                                  note_book_marks=-5000.0,
                                                                                  sub_enrich_marks=-5000.0)
                                                term_test_result.save()
                                            print ('test results successfully created for subject %s for %s' % (
                                                subject.subject_name, student_name))
                                        except Exception as e:
                                            print ('failed to create test resutls')
                                            print ('Exception 23012018-D from academics views.py %s %s' %
                                                   (e.message, type(e)))
                                if the_class.standard in middle_classes or the_class.standard in junior_classes:
                                    print('%s is in %s, which is a middle/junior class.' %
                                          (student_name, the_class.standard))
                                    test_result = TestResults(class_test=test, roll_no=student.roll_number,
                                                              student=student, marks_obtained=-5000.00, grade='')
                                    try:
                                        test_result.save()

                                        # PA, Notebook submission & Sub Enrichment to becreated only for middle
                                        if test.test_type == 'term':
                                            print ('determining whether %s is a junior or middle class' %
                                                   the_class.standard)
                                            if the_class.standard in middle_classes:
                                                print ('%s is a middle class. Hence creating PA, '
                                                       'Notebook Sub & Sub Enrich'% the_class.standard)
                                                term_test_result = TermTestResult(test_result=test_result,
                                                                                  periodic_test_marks=-5000.0,
                                                                                  note_book_marks=-5000.0,
                                                                                  sub_enrich_marks=-5000.0)
                                                term_test_result.save()
                                            else:
                                                print ('%s is a junior class. Hence not creating PA, '
                                                       'Notbook Sub & Sub enrich for %s' %
                                                       (the_class.standard, student_name))
                                        print ('test results successfully created for subject %s for %s' % (
                                            subject.subject_name, student_name))
                                    except Exception as e:
                                        print('exception 23012018-E from student views.py %s %s' % (e.message, type(e)))
                                        print('failed to save test results of subject %s for %s' %
                                              (subject.subject_name, student_name))
                    messages.success(request._request, 'successfully created tests for %s' % student_name)
                    return render(request, 'classup/mid_term_admission.html', context_dict)
                except Exception as e:
                    print ('exception 22012018-A from student views.py %s %s' % (e.message, type(e)))
                    error = 'no student is associated with admission no: %s' % admission_no
                    messages.error(request._request, error)
                    print (error)
                    context_dict['error'] = error
                    form = MidTermAdmissionForm(school_id=school_id)
                    context_dict['form'] = form
                    form.errors['__all__'] = form.error_class([error])
                    return render(request, 'classup/mid_term_admission.html', context_dict)


class StudentPromotion(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Upload Student Promotion List'
        school_id = request.session['school_id']
        print(school_id)
        school = School.objects.get(id=school_id)
        # highest_class_dict = Class.objects.filter(school=school).aggregate(Max('sequence'))
        # print(highest_class_dict['sequence__max'])
        # highest_class = Class.objects.get(school=school, sequence=highest_class_dict['sequence__max'])
        # print(highest_class)
        # try:
        #     students = Student.objects.filter(school=school, current_class=highest_class)
        #     if students.count() > 0:
        #         print(students)
        #         print('Student promotion for %s has already been done. Hence not doing again' % school.school_name)
        #         error = 'Student promotion has already been done'
        #         messages.error(request._request, 'Promotion has already been carried out.')
        #         print (error)
        #         return render(request, 'classup/setup_index.html', context_dict)
        #     else:
        #         print('Student promotion for %s has not been done. Will do now...' % school.school_name)
        #         classes = Class.objects.filter(school=school).order_by('-sequence')
        #         print('retrieved classes for %s' % school.school_name)
        #         sections = Section.objects.filter(school=school).order_by('section')
        #         print(sections)
        #         print(classes)
        #
        #         for a_class in classes:
        #             if a_class.sequence == highest_class_dict['sequence__max']:
        #                 continue
        #             for a_section in sections:
        #                 students = Student.objects.filter(current_class=a_class, current_section=a_section)
        #                 for student in students:
        #                     try:
        #                         student_name = '%s %s' % (student.fist_name, student.last_name)
        #                         try:
        #                             # the student should not be in the not promoted list.
        #                             #  Only then he/she will be promoted
        #                             entry = NPromoted.objects.get(student=student)
        #                             print('%s is  in the not_promoted. Hence not promoting...' % (student_name))
        #                             print(entry)
        #                         except Exception as e:
        #                             print('exception 04042018-B from student views.py %s %s' % (e.message, type(e)))
        #                             print('%s was not in not_promoted. Promoting now...' % (student_name))
        #                             promoted_to_class = Class.objects.get(school=school, sequence=a_class.sequence + 1)
        #                             print('%s is going to be promoted to %s-%s' %
        #                                   (student_name, promoted_to_class.standard, a_section.section))
        #                             print('%s current class is %s-%s' %
        #                                   (student_name, student.current_class.standard,
        #                                    student.current_section.section))
        #                             student.current_class = promoted_to_class
        #                             student.save()
        #                             print('%s now promoted to %s-%s' %
        #                                   (student_name, promoted_to_class.standard, a_section.section))
        #                     except Exception as e:
        #                         print('failed to promote student %s' % student.fist_name)
        #                         print('exception 04042018-A from student views.py %s %s' % (e.message, type(e)))
        #         messages.success(request._request, 'students promoted.')
        #         return render(request, 'classup/setup_index.html', context_dict)
        # except Exception as e:
        #     print('exception 04042018-C from student views.py %s %s' % (e.message, type(e)))
        #
        # return render(request, 'classup/setup_index.html', context_dict)


        form = ExcelFileUploadForm()
        context_dict['form'] = form
        return render(request, 'classup/setup_data.html', context_dict)

    def post(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Setup Time Table'

        # first see whether the cancel button was pressed
        if "cancel" in request.POST:
            return render(request, 'classup/setup_index.html', context_dict)

        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for student promotion...')
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
                    try:
                        student = Student.objects.get(school=school, student_erp_id=erp_id)
                        student_name = '%s %s' % (student.fist_name, student.last_name)
                        print('retrieved student associated with erp_id %s: %s of class %s-%s' %
                              (erp_id, student_name, student.current_class.standard, student.current_section.section))
                        try:
                            # the student should not be in the not promoted list. Only then he/she will be promoted
                            entry = NPromoted.objects.get(student=student)
                            print('%s is  in the not_promoted. Hence not promoting...' % (student_name))
                            print(entry)
                        except Exception as e:
                            print('exception 06032018-E from student views.py %s %s' % (e.message, type(e)))
                            print('%s was not in not_promoted. Promoting now...' % (student_name))
                            try:
                                # get the new class
                                new_class = sheet.cell(row, 5).value
                                new_section = sheet.cell(row, 6).value
                                print('%s is to be promoted to %s-%s' % (student_name, new_class, new_section))
                                try:
                                    student.current_class = Class.objects.get(school=school, standard=new_class)
                                    student.current_section = Section.objects.get(school=school, section=new_section)
                                    student.save()
                                    print('successfully promoted %s to %s-%s' % (student_name, new_class, new_section))

                                    # 03/04/208 - also send message to parents
                                    try:
                                        parent = student.parent.parent_name
                                        mobile = student.parent.parent_mobile1
                                        message = 'Dear %s, your ward %s is promoted to class %s-%s. ' % \
                                                  (parent, student_name, new_class, new_section)
                                        message += 'Jagarn Public School welcomes all students to new session 2018-19. '
                                        message += 'Regards, Dr D.K. Sinha, Principal, JPS Noida'
                                        print(message)
                                        #sms.send_sms1(school, 'admin@jps.com', mobile, message, 'Student Promotion')
                                        print('sent Student promotion message to %s, parent of %s' %
                                              (parent, student_name))
                                    except Exception as e:
                                        print('failed to send Student Prmotion sms for %s' % student_name)
                                        print('exception 03042018-A from student views.py %s (%s)' %
                                              (e.message, type(e)))
                                except Exception as e:
                                    print('failed to promote %s to %s-%s' % (student_name, new_class, new_section))
                                    print('exception 06032018-B from student views.py %s %s' % (e.message, type(e)))
                            except Exception as e:
                                print('failed to add %s (%s) to not_promoted' % (student_name, erp_id))
                                print('exception 06032018-C from student views.py %s %s' % (e.message, type(e)))
                    except Exception as e:
                        print('failed to retrieve student with erp_id %s' % erp_id)
                        print('exception 06032018-A from student views.py %s %s' % (e.message, type(e)))
                messages.success(request._request, 'uploaded list of promoted students')
                context_dict['status'] = 'success'
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 04032018-G from student views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)


class NotPromoted(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Upload Not Promoted Student List'
        form = ExcelFileUploadForm()
        context_dict['form'] = form
        return render(request, 'classup/setup_data.html', context_dict)

    def post(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Setup Time Table'

        # first see whether the cancel button was pressed
        if "cancel" in request.POST:
            return render(request, 'classup/setup_index.html', context_dict)

        school_id = request.session['school_id']
        school = School.objects.get(id=school_id)

        # get the file uploaded by the user
        form = ExcelFileUploadForm(request.POST, request.FILES)
        context_dict['form'] = form

        if form.is_valid():
            try:
                print ('now starting to process the uploaded file for student not_promotion...')
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
                    # 26/03/2018 - Now we store some additional details like compartment subject, detained etc
                    details = sheet.cell(row, 4).value
                    try:
                        student = Student.objects.get(school=school, student_erp_id=erp_id)
                        student_name = '%s %s' % (student.fist_name, student.last_name)
                        print('retrieved student associated with erp_id %s: %s of class %s-%s' %
                              (erp_id, student_name, student.current_class.standard, student.current_section.section))
                        try:
                            entry = NPromoted.objects.get(student=student)
                            print('%s is already in the not_promoted. Not adding...' % (student_name))
                            print(entry)
                        except Exception as e:
                            print('%s was not in not_promoted. Adding now...' % (student_name))
                            print('exception 04032018-E from student views.py %s %s' % (e.message, type(e)))
                            try:
                                entry = NPromoted(student=student, details=details)
                                entry.save()
                                print('With sorrow :(, added %s to not_promoted. Details: %s ' %
                                      (student_name, details))
                            except Exception as e:
                                print('failed to add %s (%s) to not_promoted' % (student_name, erp_id))
                                print('exception 04032018-F from student views.py %s %s' % (e.message, type(e)))
                    except Exception as e:
                        print('failed to retrieve student with erp_id %s' % erp_id)
                        print('exception 04032018-G from student views.py %s %s' % (e.message, type(e)))
                messages.success(request._request, 'uploaded list of not_cleared students')
                context_dict['status'] = 'success'
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 04032018-G from student views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)
