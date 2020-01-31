import xlrd
import xlsxwriter
from rest_framework import generics

from authentication.views import JSONResponse
from setup.models import School
from student.models import Student
from exam.models import CBSERollNo


class CBSEMapping(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        print ('now starting to process the uploaded file CBSE Roll No mapping to student ERP Id...')
        fileToProcess_handle = request.FILES['JPS_CBSE_mapping.xlsx']
        print(fileToProcess_handle)

        fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
        sheet = fileToProcess.sheet_by_index(0)
        for row in range(sheet.nrows):
            # first two rows are header rows
            if row == 0:
                school_id = sheet.cell(row, 0).value
                school = School.objects.get(pk=school_id)
                print('school = %s' % school)
                continue
            print ('Processing a new row')
            try:
                erp_id = sheet.cell(row, 0).value
                decimal = '.'
                if decimal in erp_id:
                    print('student id contains a decimal followed by zero. This has to be removed')
                    erp_id = erp_id[:-2]
                    print('decimal and following zero removed. Now student_id = %s' % erp_id)
            except Exception as e:
                print('exception 31012020-A from exam cbse.py. %s %s' % (e.message, type(e)))

            try:
                student = Student.objects.get(school=school, student_erp_id=erp_id)
                print('mapping the CBSE Roll No for %s with erp_id %s' % (student, erp_id))
                cbse_roll_no = str(int(sheet.cell(row, 1).value))
                print('cbse_roll_no = %s' % str(cbse_roll_no))
                try:
                    cbse = CBSERollNo.objects.get(student=student)
                    print('cbse mapping for %s already exist. This will be updated now...' % student)
                    cbse.cbse_roll_no = str(cbse_roll_no)
                    cbse.save()
                    print('updated the cbse mapping for %s' % student)
                except Exception as e:
                    print('exception 31012020-B from exam cbse.py %s %s' % (e.message, type(e)))
                    print('cbse mapping for %s was not done till before. Doing now')
                    cbse = CBSERollNo(student=student)
                    cbse.cbse_roll_no = str(cbse_roll_no)
                    cbse.save()
                    print('created cbse mapping for %s' % student)
            except Exception as e:
                print('could not retrieve student associated with erp_id %s' % str(erp_id))
        return JSONResponse({'status': 'ok'}, status=200)
