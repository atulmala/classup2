
# Create your views here.

import StringIO
import xlsxwriter

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.http import HttpResponse
from django.shortcuts import render

from setup.models import School
from academics.models import ClassTest
from exam.forms import ResultSheetForm
from .models import Student, Parent

from .serializers import StudentSerializer, ParentSerializer

from authentication.views import JSONResponse

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
            form = ResultSheetForm(request.POST, school_id=school_id)

            if form.is_valid():
                the_class = form.cleaned_data['the_class']
                section = form.cleaned_data['section']
                print ('result sheet will be generated for %s-%s' % (the_class.standard, section.section))

                excel_file_name = 'Student_List' + str(the_class.standard) + '-' + str(section.section) + '.xlsx'

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
                header = workbook.add_format({
                    'bold': True,
                    'bg_color': '#F7F7F7',
                    'color': 'black',
                    'align': 'center',
                    'valign': 'top',
                    'border': 1
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
                perc_format = workbook.add_format({
                    'num_format': '0.00%',
                    'align': 'center',
                    'valign': 'top',
                    'border': 1
                })
                cell_grade = workbook.add_format({
                    'align': 'center',
                    'valign': 'top',
                    'bold': True,
                    'border': 1
                })

                row = 0
                col = 0
                sheet.write_string (row, col, 'S No', title)
                col = col + 1
                sheet.set_column ('B:B', 16)
                sheet.write_string (row, col, 'Admission No', title)
                col = col + 1
                sheet.set_column ('C:C', 20)
                sheet.write_string (row, col, 'Student Name', title)

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
                        student_name = student.fist_name + ' ' + student.last_name
                        sheet.write_string (row, col, student_name, cell_normal)

                        # set border for the next col. No value goes inside the cell.
                        col = col + 1
                        sheet.write_string (row, col, '', cell_normal)

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