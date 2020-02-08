# Create your views here.

import StringIO
import xlsxwriter
import xlrd
import json
import datetime

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Max

from formats.formats import Formats as format
from setup.models import School, Configurations
from academics.models import ClassTest, TestResults, TermTestResult, ThirdLang, Class, Section, CoScholastics
from exam.models import HigherClassMapping, NPromoted
from exam.forms import ResultSheetForm
from bus_attendance.models import Student_Rout, BusUser
from erp.models import CollectAdmFee
from .models import Student, Parent, DOB, AdditionalDetails, House

from setup.forms import ExcelFileUploadForm
from .forms import MidTermAdmissionForm

from setup.views import validate_excel_extension

from .serializers import StudentSerializer, ParentSerializer, StudentDetailSerializer

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

        if the_class != 'in_params':
            q1 = Student.objects.filter(school=school, current_section__section=section,
                                        current_class__standard=the_class, active_status=True)
            q2 = q1.order_by('fist_name', 'last_name')
            return q2
        else:
            print('getting the student list for %s for fees payment' % school)
            reg_no = self.request.GET.get('reg_no')
            print(reg_no)
            if reg_no != '':
                try:
                    q1 = Student.objects.filter(school=school, student_erp_id=reg_no)
                    return q1
                except Exception as e:
                    print('exception 02032019-A from student views.py %s %s' % (e.message, type(e)))
                    print('failed to retrieve student with reg_no: %s' % reg_no)
            else:
                first_name = self.request.GET.get('first_name')
                the_class = self.request.GET.get('the_class')
                current_class = Class.objects.get(school=school, standard=the_class)

                try:
                    q1 = Student.objects.filter(school=school, fist_name__icontains=first_name,
                                                current_class=current_class, active_status=True)
                    q2 = q1.order_by('fist_name')
                    return q2
                except Exception as e:
                    print('exception 02032019-B from student views.py %s %s' % (e.message, type(e)))
                    print('failed to retrieve student list for matching name %s of class %s ' %
                          (first_name, the_class))


class SingleStudentDetails(generics.ListAPIView):
    serializer_class = StudentDetailSerializer

    def get_queryset(self):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        student_id = self.request.query_params.get('student_id')
        print(student_id)
        query_set = Student.objects.filter(school=school, student_erp_id=student_id)
        return query_set


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
        q2 = q1.order_by('fist_name', 'last_name')
        return q2


class ParentInquiry(generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        parents = Parent.objects.all()
        students = Student.objects.all()
        print('parents count = %i' % parents.count())
        print('student count %i' % students.count())
        print('extra parents = %i' % (parents.count() - students.count()))
        extra_parent_count = parents.count()
        deleted_count = 0

        for p in parents:
            found = False
            for s in students:
                if s.parent.pk == p.pk:
                    extra_parent_count -= 1
                    found = True
                    break
            if not found:
                found = False
                print('parent %s with mobile number %s is not associated with any student' %
                      (p.parent_name, p.parent_mobile1))
                print('hence, this parent and associated user will be delted')

                # delete the user & parent
                try:
                    user = User.objects.get(username=p.parent_mobile1)
                    p.delete()
                    print('parent deleted')
                    user.delete()
                    print('user deleted')

                    deleted_count += 1
                except Exception as e:
                    print('failed to delete user/parent')
                    print('exception 18032019-X from student views.py %s %s' % (e.message, type(e)))

        print('total number of extra parents = %i' % extra_parent_count)
        context_dict = {}
        context_dict['extra_parents'] = extra_parent_count
        context_dict['deleted_count'] = deleted_count
        return JSONResponse(context_dict, status=200)


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
    student_detail = {

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


class StudentListDownload(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        data = json.loads(request.body)
        print(data)
        school_id = data['school_id']
        school = School.objects.get(id=school_id)
        whole_school = data['whole_school']
        print(whole_school)
        standard = data['the_class']
        if standard != '':
            the_class = Class.objects.get(school=school, standard=standard)
        sec = data['section']
        if sec != '':
            section = Section.objects.get(school=school, section=sec)
        all_sections = data['all_sections']
        print(all_sections)

        if whole_school:
            excel_file_name = 'Student_List.xlsx'
            students = Student.objects.filter(school=school,
                                              active_status=True).order_by('current_class__sequence',
                                                                           'current_section', 'fist_name', 'last_name')
        else:
            if all_sections:
                excel_file_name = '%s_Student_List.xlsx' % (the_class)
                students = Student.objects.filter(school=school, current_class=the_class,
                                                  active_status=True).order_by('current_class__sequence',
                                                                               'current_section', 'fist_name',
                                                                               'last_name')
            else:
                excel_file_name = '%s_%s_Student_List.xlsx' % (the_class, section)
                students = Student.objects.filter(school=school, current_class=the_class, current_section=section,
                                                  active_status=True).order_by('fist_name', 'last_name')

        print (students.count())

        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Student List')
        sheet.set_paper(9)
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.repeat_rows(0)
        header_text = '%s Student List as on &D(mm/dd/yy)' % (school)
        sheet.set_header('&C%s' % header_text, {'font_size': 22})
        sheet.set_footer('&RPage of &P of &N')

        fmt = format()
        title = workbook.add_format(fmt.get_title())
        title.set_border()
        cell_left = workbook.add_format(fmt.get_cell_normal())
        cell_left.set_border()
        cell_left = workbook.add_format(fmt.get_cell_left())
        cell_left.set_border()
        cell_center = workbook.add_format(fmt.get_cell_center())
        cell_center.set_border()
        small_cell = workbook.add_format(fmt.get_cell_small())

        row = 0
        col = 0
        sheet.write_string(row, col, 'S No', title)
        col = col + 1
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 12)
        sheet.write_string(row, col, 'Admission No', title)
        col = col + 1
        sheet.set_column('C:D', 10)
        sheet.write_string(row, col, 'First Name', title)
        col += 1
        sheet.write_string(row, col, 'SurName', title)
        col += 1
        sheet.set_column('E:F', 8)
        sheet.write_string(row, col, 'Class', title)
        col += 1
        sheet.write_string(row, col, 'Section', title)
        col += 1
        sheet.set_column('G:G', 10)
        sheet.write_string(row, col, 'DOB(dd/mm/yy)', title)
        col += 1
        sheet.set_column('H:K', 15)
        sheet.write_string(row, col, 'Father Name', title)
        col += 1
        sheet.write_string(row, col, 'Father Mobile', title)
        col += 1
        sheet.write_string(row, col, 'Mother Name', title)
        col += 1
        sheet.write_string(row, col, 'Mother Mobile', title)
        col += 1
        sheet.set_column('L:L', 30)
        sheet.write_string(row, col, 'Address', title)
        col += 1
        sheet.write_string(row, col, 'House', title)
        col += 1
        sheet.set_column('N:N', 10)
        sheet.write_string(row, col, 'Bus Rout', title)
        col += 1
        sheet.set_column('O:O', 16)
        sheet.write_string(row, col, 'Bus Stop', title)
        col += 1

        row = row + 1
        col = 0
        s_no = 1
        for student in students:
            sheet.write_number(row, col, s_no, cell_left)
            col += 1
            sheet.write_string(row, col, student.student_erp_id, cell_left)
            col += 1
            sheet.write_string(row, col, student.fist_name, cell_left)
            col += 1
            sheet.write_string(row, col, student.last_name, cell_left)
            col += 1
            current_class = student.current_class.standard
            sheet.write_string(row, col, current_class, cell_center)
            col += 1
            current_section = student.current_section.section
            sheet.write_string(row, col, current_section, cell_center)
            col += 1
            try:
                d = DOB.objects.get(student=student)
                dob = d.dob
                sheet.write_string(row, col, dob.strftime('%d/%m/%Y'), cell_left)
            except Exception as e:
                print('exception 03072019-A from student views.py %s %s' % (e.message, type(e)))
                print('dob for %s not entered' % student)
                sheet.write_string(row, col, 'Not Entered', cell_left)
            col += 1
            parent = student.parent.parent_name
            sheet.write_string(row, col, parent, cell_left)
            col += 1
            mobile = student.parent.parent_mobile1
            sheet.write_string(row, col, mobile, cell_left)
            col += 1
            try:
                a = AdditionalDetails.objects.get(student=student)
                mother_name = a.mother_name
                sheet.write_string(row, col, mother_name, cell_left)
            except Exception as e:
                print('exception 03072019-B from student views.py %s %s' % (e.message, type(e)))
                print('mother name not entered for %s' % student)
                sheet.write_string(row, col, 'Not Entered', cell_left)
            col += 1
            mobile2 = student.parent.parent_mobile2
            if mobile2 == '1234567890':
                mobile2 = 'Not Entered'
            sheet.write_string(row, col, mobile2, cell_left)
            col += 1
            try:
                a = AdditionalDetails.objects.get(student=student)
                address = a.address
                sheet.write_string(row, col, address, small_cell)
            except Exception as e:
                print('exception 03072019-C from student views.py %s %s' % (e.message, type(e)))
                print('address name not entered for %s' % student)
                sheet.write_string(row, col, 'Not Entered', cell_left)
            col += 1
            try:
                h = House.objects.get(student=student)
                house = h.house
                sheet.write_string(row, col, house, cell_left)
            except Exception as e:
                print('exception 03072019-D from student views.py %s %s' % (e.message, type(e)))
                print('house not entered for %s' % student)
                sheet.write_string(row, col, 'Not Entered', cell_left)
            col += 1
            try:
                sr = Student_Rout.objects.get(student=student)
                bus_rout = sr.bus_root.bus_root
                sheet.write_string(row, col, bus_rout, cell_left)
                col += 1
                bus_stop = sr.bus_stop.stop_name
                sheet.write_string(row, col, bus_stop, cell_left)
                col += 1
            except Exception as e:
                print('exception 03072019-E from student views.py %s %s' % (e.message, type(e)))
                print('bus rout or bus stop not entered for %s' % student)
                sheet.write_string(row, col, 'Not Entered', cell_left)
                col += 1
                sheet.write_string(row, col, 'Not Entered', cell_left)
            row = row + 1
            s_no = s_no + 1
            col = 0
        workbook.close()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
        response.write(output.getvalue())
        return response


class MidTermAdmission(generics.ListCreateAPIView):
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
                    tests = ClassTest.objects.filter(the_class=the_class, section=section)
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
                                                              student=student, marks_obtained=-5000.00, grade='')
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
                                                       'Notebook Sub & Sub Enrich' % the_class.standard)
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
                    # now create co-scholastic grades entry
                    terms = ['term1', 'term2']
                    for term in terms:
                        try:
                            coscholastic = CoScholastics.objects.get(term=term, the_class=the_class,
                                                                     section=section, student=student)
                            print('coscholastic for %s already exist for %s. Hence not creating' % (term, student))
                        except Exception as e:
                            print('exception 04042019-A from student views.py %s %s' % (e.message, type(e)))
                            print('coscholastic for %s does not exist for %s. Hence crating...' % (term, student))
                            coscholastic = CoScholastics(term=term, the_class=the_class,
                                                         section=section, student=student)
                            coscholastic.save()
                            print('coscholastic for %s for %s successfully created mid term admission' % (
                                term, student))

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
        highest_class_dict = Class.objects.filter(school=school).aggregate(Max('sequence'))
        print(highest_class_dict['sequence__max'])
        highest_class = Class.objects.get(school=school, sequence=highest_class_dict['sequence__max'])
        print(highest_class)
        try:
            students = Student.objects.filter(school=school, current_class=highest_class)
            if students.count() > 0:
                print(students)
                print('Student promotion for %s has already been done. Hence not doing again' % school.school_name)
                error = 'Student promotion has already been done'
                messages.error(request._request, 'Promotion has already been carried out.')
                print (error)
                return render(request, 'classup/setup_index.html', context_dict)
            else:
                print('Student promotion for %s has not been done. Will do now...' % school.school_name)
                classes = Class.objects.filter(school=school).order_by('-sequence')
                print('retrieved classes for %s' % school.school_name)
                sections = Section.objects.filter(school=school).order_by('section')
                print(sections)
                print(classes)

                for a_class in classes:
                    if a_class.sequence == highest_class_dict['sequence__max']:
                        continue
                    for a_section in sections:
                        students = Student.objects.filter(current_class=a_class, current_section=a_section)
                        for student in students:
                            try:
                                student_name = '%s %s' % (student.fist_name, student.last_name)
                                try:
                                    # the student should not be in the not promoted list.
                                    #  Only then he/she will be promoted
                                    entry = NPromoted.objects.get(student=student)
                                    print('%s is  in the not_promoted. Hence not promoting...' % (student_name))
                                    print(entry)
                                except Exception as e:
                                    print('exception 04042018-B from student views.py %s %s' % (e.message, type(e)))
                                    print('%s was not in not_promoted. Promoting now...' % (student_name))
                                    promoted_to_class = Class.objects.get(school=school, sequence=a_class.sequence + 1)
                                    print('%s is going to be promoted to %s-%s' %
                                          (student_name, promoted_to_class.standard, a_section.section))
                                    print('%s current class is %s-%s' %
                                          (student_name, student.current_class.standard,
                                           student.current_section.section))
                                    student.current_class = promoted_to_class
                                    student.save()
                                    print('%s now promoted to %s-%s' %
                                          (student_name, promoted_to_class.standard, a_section.section))
                            except Exception as e:
                                print('failed to promote student %s' % student.fist_name)
                                print('exception 04042018-A from student views.py %s %s' % (e.message, type(e)))
                messages.success(request._request, 'students promoted.')
                return render(request, 'classup/setup_index.html', context_dict)
        except Exception as e:
            print('exception 04042018-C from student views.py %s %s' % (e.message, type(e)))

        return render(request, 'classup/setup_index.html', context_dict)

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
                                        # sms.send_sms1(school, 'admin@jps.com', mobile, message, 'Student Promotion')
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
                            print('%s is already in the not_promoted. Not adding only changing details...' %
                                  (student_name))
                            entry.details = details
                            entry.save()
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


class AddStudent(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['header'] = 'Student Addition Web'
        try:
            data = json.loads(request.body)
            print(data)

            print('Student Addition from web - process started')
            school_id = data['school_id']
            try:
                school = School.objects.get(pk=school_id)
                print('new student to be added to %s' % school)
            except Exception as e:
                print('exception 07082019-A from student views.py %s %s' % (e.message, type(e)))
                print('failed to determine school')
                context_dict['status'] = 'fail'
                context_dict['message'] = 'failed to determine school'
                return JSONResponse(context_dict, status=201)
            sender = data['sender']
            reg_no = data['reg_no']
            # ensure that the registration number is unique
            try:
                already = Student.objects.get(school=school, student_erp_id=reg_no)
                the_class = already.current_class.standard
                section = already.current_section.section
                print('reg no %s is already associated with %s of %s-%s' % (reg_no, already, the_class, section))
                context_dict['status'] = 'fail'
                context_dict['message'] = 'Reg No %s is already associated with %s of class %s-%s' % \
                                          (reg_no, already, the_class, section)
                return JSONResponse(context_dict, status=201)
            except Exception as e:
                print('exception 07082019-B from student views.py %s %s' % (e.message, type(e)))
                print('Reg no %s is available' % reg_no)
            first_name = data['first_name']
            last_name = data['last_name']
            cls = data['the_class']
            the_class = Class.objects.get(school=school, standard=cls)
            sec = data['section']
            section = Section.objects.get(school=school, section=sec)
            father_name = data['father_name']
            father_mobile = data['father_mobile']
            mother_mobile = data['mother_mobile']
            email = data['email']

            # check if this parent already exist
            try:
                parent = Parent.objects.get(parent_mobile1=father_mobile)
                print('parent %s already exist. Hence will not be created' % parent)
                new_user = False
            except Exception as e:
                print('exception 07082019-C from student views.py %s %s' % (e.message, type(e)))
                print('parent %s does not exist. Hence parent and user object to be created' % father_name)
                parent = Parent(parent_name=father_name, parent_mobile1=father_mobile,
                                parent_mobile2=mother_mobile, parent_email=email)
                parent.save()
                print('created parent for %s. Now creating user' % father_name)
                if User.objects.filter(username=father_mobile).exists():
                    print('user for parent %s with mobile %s already exist.' % (father_name, father_mobile))
                else:
                    new_user = True
                    # the user name would be the mobile, and password would be a random string
                    password = User.objects.make_random_password(length=5, allowed_chars='1234567890')

                    print ('Initial password = %s' % password)
                    if email == '':
                        email = 'dummy@classup.in'
                    user = User.objects.create_user(father_mobile, email, password)
                    user.first_name = father_name
                    user.is_staff = False
                    user.save()
                    print('user created for parent %s with mobile %s.' % (father_name, father_mobile))
            # create student basic record
            try:
                student = Student(school=school, student_erp_id=reg_no, fist_name=first_name,
                                  last_name=last_name, parent=parent, current_class=the_class, current_section=section)
                student.save()
                print('created basic record for %s %s. Will send welcome message to parent now' %
                      (first_name, last_name))
            except Exception as e:
                print('exception 07082019-D from student view.py %s %s' % (e.message, type(e)))
                print('failed in creating basic student record')
                context_dict['status'] = 'fail'
                message = 'Failed to add student. Please try contact ClassUp Support error 070082019-B %s' % \
                          e.message
                context_dict['message'] = message
                return JSONResponse(context_dict, status=201)
            if new_user:
                conf = Configurations.objects.get(school=school)
                android_link = conf.google_play_link
                iOS_link = conf.app_store_link
                message = 'Dear %s, Welcome to ClassUp. ' % father_name
                message += "Now you can track your child's progress at %s ." % school.school_name
                message += 'Your user id is: %s, and password is %s' % (str(father_mobile), str(password))
                message += '. Please install ClassUp from these links. Android: %s, iOS: %s' % \
                           (android_link, iOS_link)
                message += '. For support, email to: support@classup.in'
                print(message)
                message_type = 'Welcome Parent (Web Interface)'

                sms.send_sms1(school, sender, str(father_mobile), message, message_type)

            # create additional details
            date_of_birth = data['dob']
            try:
                date = datetime.datetime.strptime(date_of_birth, '%Y-%m-%d')
                dob = DOB(student=student, dob=date)
                dob.save()
                print('dob set for %s as %s' % (student, date_of_birth))
            except Exception as e:
                print('exception 07082019-E from student views.py %s %s' % (e.message, type(e)))
                print('failed in setting up date of birth for %s of %s' % (student, school))

            date_of_admission = data['date_of_admission']
            gender = data['gender']
            mother_name = data['mother_name']
            adhar = data['adhar']
            blood_group = data['blood_group']
            house = data['house']
            father_occupation = data['father_occupation']
            mother_occupation = data['mother_occupation']
            address = data['address']
            try:
                additional_details = AdditionalDetails(student=student, gender=gender,
                                                       date_of_admission=date_of_admission, mother_name=mother_name,
                                                       adhar=adhar, blood_group=blood_group,
                                                       father_occupation=father_occupation,
                                                       mother_occupation=mother_occupation, address=address)
                additional_details.save()
                print('saved additional details for %s' % student)
            except Exception as e:
                print('exception 07082019-F from student views.py %s %s' % (e.message, type(e)))
                print('failed to save additional details for %s' % student)

            # the bus user data
            transport = data['transport']
            if transport == 'bus_user':
                bus_user = BusUser(student=student)
                bus_user.save()
                print('%s is bus user' % student)

            try:
                entry = CollectAdmFee.objects.get(school=school, student=student)
                print('%s has been already marked for collecting admission fee' % student)
            except Exception as e:
                print('exception 08082019-A-A from student views.py %s %s' % (e.message, type(e)))
                print('%s will be now marked for collecting admission fee' % student)
                entry = CollectAdmFee(school=school, student=student)
                entry.save()

            print('all data for student %s added and admission & other one time fee to be collected' % student)
            context_dict['status'] = 'success'
            context_dict['message'] = 'student %s successfully added' % student
            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('exception 07082019-F from student views.py %s %s' % (e.message, type(e)))
            print('probably json decoding error while adding student')
            context_dict['status'] = 'fail'
            context_dict['message'] = 'failed to add student'
            return JSONResponse(context_dict, status=201)


class UpdateStudent(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['header'] = 'Student Update Web'
        try:
            data = json.loads(request.body)
            print(data)

            print('Student Update from web - process started')
            school_id = data['school_id']

            school = School.objects.get(pk=school_id)

            sender = data['sender']
            reg_no = data['reg_no']

            # retrieve the student
            student = Student.objects.get(school=school, student_erp_id=reg_no)
            the_class = student.current_class.standard
            section = student.current_section.section
            print('retrieved student with reg no %s of %s-%s. This will be updated now...' %
                  (reg_no, the_class, section))

            first_name = data['first_name']
            student.fist_name = first_name
            last_name = data['last_name']
            student.last_name = last_name
            cls = data['the_class']
            the_class = Class.objects.get(school=school, standard=cls)
            student.current_class = the_class
            sec = data['section']
            section = Section.objects.get(school=school, section=sec)
            student.current_section = section
            student.save()

            # parent update
            father_name = data['father_name']
            new_mobile = data['father_mobile']
            email = data['email']
            # retrieve current mobile of this parent
            parent = student.parent
            parent.parent_name = father_name
            current_mobile = parent.parent_mobile1
            parent.parent_email = email
            if new_mobile != current_mobile:
                print('mobile number of this student parent is changed. New user has to be created ')
                try:
                    user = User.objects.get(username=current_mobile)
                    user.username = new_mobile

                    # need to generate a new password and communicate to the parent
                    password = User.objects.make_random_password(length=5, allowed_chars='1234567890')
                    user.set_password(password)
                    user.save()
                    conf = Configurations.objects.get(school=school)
                    android_link = conf.google_play_link
                    iOS_link = conf.app_store_link
                    message = 'Dear %s, your details for ClassUp app are updated. ' % father_name
                    message += 'New user id is %s password is %s ' % (new_mobile, password)
                    message += '. Please install ClassUp from these links. Android: '
                    message += android_link
                    message += '. iPhone/iOS: '
                    message += iOS_link
                    message += ' For any help please send email to info@classup.in. Regards, ClassUp Support'
                    print('message = %s' % message)
                    message_type = 'Update Student/Parent'
                    sms.send_sms1(school, sender, str(new_mobile), message, message_type)
                except Exception as e:
                    print('exception 16112019-B from student views.py %s %s' % (e.message, type(e)))
                    print('parent user with mobile number %s does not exist' % current_mobile)
                parent.parent_mobile1 = new_mobile
            mother_mobile = data['mother_mobile']
            parent.parent_mobile2 = mother_mobile
            parent.save()
            student.parent = parent
            student.save()

            # update additional details
            date_of_birth = data['dob']
            try:
                date = datetime.datetime.strptime(date_of_birth, '%Y-%m-%d')
                dob = DOB.objects.get(student=student)
                dob.dob = date
                dob.save()
                print('dob updated for %s as %s' % (student, date_of_birth))
            except Exception as e:
                print('exception 16112019-C from student views.py %s %s' % (e.message, type(e)))
                print('date of birth for %s of %s was not set before. Setting now...' % (student, school))
                dob = DOB(student=student)
                dob.dob = date
                dob.save()
                print('date of birth for %s of %s is not set to %s' % (student, school, date_of_birth))

            gender = data['gender']
            mother_name = data['mother_name']
            adhar = data['adhar']
            blood_group = data['blood_group']
            house = data['house']
            father_occupation = data['father_occupation']
            mother_occupation = data['mother_occupation']
            address = data['address']
            try:
                additional_details = AdditionalDetails.objects.get(student=student)
            except Exception as e:
                print('exception 16112019-D from student views.py %s %s' % (e.message, type(e)))
                print('additional details for %s were not created before. Creating now...' % student)
                additional_details = AdditionalDetails(student=student)
            additional_details.gender = gender
            additional_details.mother_name = mother_name
            additional_details.adhar = adhar
            additional_details.blood_group = blood_group
            additional_details.father_occupation = father_occupation
            additional_details.mother_occupation = mother_occupation
            additional_details.address = address
            additional_details.save()
            print('updated additional details for %s' % student)

            # the bus user data
            transport = data['transport']
            if transport == 'bus_user':
                try:
                    bus_user = BusUser.objects.get(student=student)
                    bus_user.save()
                    print('%s is bus user' % student)
                except Exception as e:
                    print('exception 16112019-D from student views.py %s %s' % (e.message, type(e)))
                    print('%s was not a bus user earlier. Now setting as bus user...' % student)
                    bus_user = BusUser(student=student)
                    bus_user.save()
                    print('%s is now a bus user' % student)
            if transport == 'walker':
                try:
                    bus_user = BusUser.objects.get(student=student)
                    bus_user.delete()
                except Exception as e:
                    print('exception 17112019-A from student views.py %s %s' % (e.message, type(e)))
                    print('%s was not a bus user either.' % student)
            context_dict['status'] = 'success'
            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('exception 07082019-F from student views.py %s %s' % (e.message, type(e)))
            print('probably json decoding error while adding student')
            context_dict['status'] = 'fail'
            context_dict['message'] = 'failed to add student'
            return JSONResponse(context_dict, status=201)
