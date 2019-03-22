import os
import xlrd

from google.cloud import storage


from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from datetime import datetime

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics

from setup.forms import ExcelFileUploadForm
from setup.views import validate_excel_extension

from setup.models import School
from student.models import Student, AdditionalDetails, House
from .models import CollectAdmFee, FeePaymentHistory, PreviousBalance

# Create your views here.


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class JSONResponse(HttpResponse):
    """
    an HttpResponse that renders its contents to JSON
    """
    def __init__(self, data, **kwargs):
        print ('from JSONResponse...')
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class SetupAddDetails(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Setup Additional Detals'
        form = ExcelFileUploadForm()
        context_dict['form'] = form
        return render(request, 'classup/setup_data.html', context_dict)

    def post(self, request, *args, **kwargs):
        print ('from class based view')
        context_dict = {

        }
        context_dict['user_type'] = 'school_admin'
        context_dict['school_name'] = request.session['school_name']
        context_dict['header'] = 'Setup Additional Details'

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
                print ('now starting to process the uploaded file for additional details...')
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
                    # first two rows are header rows
                    if row < 1:
                        continue
                    print ('Processing a new row')
                    try:
                        erp_id = sheet.cell(row, 1).value
                        mother_name = sheet.cell(row, 4).value
                        address = sheet.cell(row, 5).value
                        house = sheet.cell(row, 7).value
                    except Exception as e:
                        print('exception 19032018-E from erp views. %s %s' % (e.message, type(e)))

                    try:
                        student = Student.objects.get(school=school, student_erp_id=erp_id)
                        student_name = '%s %s of class %s-%s' % (student.fist_name, student.last_name,
                                                                 student.current_class.standard,
                                                                 student.current_section.section)
                        print('setting the additional details for %s with erp_id %s' % (student_name, erp_id))
                        try:
                            ad = AdditionalDetails.objects.get(student=student)
                            print('additional details for %s with erp_id %s are already set. Those will be updated'
                                  % (erp_id, student_name))
                            ad.mother_name = mother_name
                            ad.address = address
                            ad.save()
                            print('successfully updated the additional details for %s' % student_name)
                        except Exception as e:
                            print('exception 19032018-A from erp views.py %s %s' % (e.message, type(e)))
                            print('additional details for %s with erp_id %s were not set. Setting now...' %
                                  (student_name, erp_id))
                            ad = AdditionalDetails(student=student, mother_name=mother_name, address= address)
                            ad.save()
                            print('successfully created additional details for %s with erp_id %s' %
                                  (student_name, erp_id))
                        print('setting the house details for %s with erp_id %s' % (student_name, erp_id))

                        try:
                            h = House.objects.get(student=student)
                            print('house details for %s with erp_id %s are already set. Those will be updated' %
                                  (erp_id, student_name))
                            h.house = house
                            h.save()
                            print('successfully updated the house details for %s' % student_name)
                        except Exception as e:
                            print('exception 28032018-A from erp views.py %s %s' % (e.message, type(e)))
                            print('house details for %s with erp_id %s were not set. Setting now...' %
                                  (student_name, erp_id))
                            h = House(student=student, house=house)
                            h.save()
                            print('successfully set house %s for student %s with erp_id %s' %
                                  (house, student_name, erp_id))
                    except Exception as e:
                        print('exception 19032018-B from erp views.py %s %s' % (e.message, type(e)))
                        print('no student associated with erp_id %s' % erp_id)
                    row += 1
                    # file upload and saving to db was successful. Hence go back to the main menu
                messages.success(request._request, 'Additional Details Successfully uploaded')
                return render(request, 'classup/setup_index.html', context_dict)
            except Exception as e:
                error = 'invalid excel file uploaded.'
                print (error)
                print ('exception 19032018-D from erp views.py %s %s ' % (e.message, type(e)))
                form.errors['__all__'] = form.error_class([error])
                return render(request, 'classup/setup_data.html', context_dict)


class FeePayment(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        school_id = self.kwargs['school_id']
        student_id = self.kwargs['student_id']
        q1 = [4, 5, 6]
        q2 = [7, 8, 9]
        q3 = [10, 11, 12]
        q4 = [1, 2, 3]
        try:
            school = School.objects.get(pk=school_id)
            student = Student.objects.get(school=school, student_erp_id=student_id)
            context_dict['reg_no'] = student.student_erp_id
            full_name = '%s %s' % (student.fist_name, student.last_name)
            context_dict['full_name'] = full_name
            parent = student.parent.parent_name
            context_dict['parent'] = parent
            current_class = student.current_class.standard
            current_section = student.current_section.section
            context_dict['current_class'] = '%s %s' % (current_class, current_section)
            currentDay = datetime.now().day
            year = datetime.now().year
            month = datetime.now().month
            print(month)
            currentMonth = datetime.now().month
            print(currentMonth)
            print('processing fee payment for %s of %s of class %s as o %i-%i-%i' %
                  (student, school, current_class, currentDay, month, year))
            transaction_date = '%i/%i/%i' % (currentDay, month, year)
            context_dict['transaction_date'] = transaction_date
            storage_client = storage.Client()
            bucket = storage_client.get_bucket('classup')
            print(bucket)
            fee_file = '%s.xlsx' % str(school_id)
            fee_file_path = 'classup2/Fee/%s/%s' % (str(school_id), fee_file)
            blob = bucket.blob(fee_file_path)
            local_path = 'erp/%s' % fee_file
            blob.download_to_filename(local_path)
            wb = xlrd.open_workbook(local_path)
            sheet = wb.sheet_by_name(current_class)
            heads_array = []

            due_this_term = 0.0
            for row in range(sheet.nrows):
                if row == 0:
                    fee_frequency = sheet.cell(row, 1).value
                    d_date = sheet.cell(row, 3).value
                    continue
                if row == 1:
                    continue
                head = {}
                h = sheet.cell(row, 0).value
                amt = sheet.cell(row, 1).value
                freq = sheet.cell(row, 2).value
                if int(freq) == 0:
                    # this is one time fee (admission/caution). check if this fee to be charged for this student
                    print('%s is one time fees. checking whether it has been paid or not' % h)
                    try:
                        if CollectAdmFee.objects.get(student=student).exists():
                            print('%s has NOT paid one time fees %s' % (student, h))
                            due_this_term += amt
                    except Exception as e:
                        print('exception 21032019-A from erp views.py %s %s' % (e.message, type(e)))
                        print('%s has paid one time fees %s' % (student, h))
                        amt = 'N/A'

                if int(freq) == 12:
                    # this is once in a year fee like annual fee, exam fee etc. this is to be charge in April
                    print('%s is annual fees' % h)
                    if month == 'April':
                        head['amount'] = amt
                        due_this_term += amt
                    else:
                        amt = 'N/A'
                if int(freq) == 1:
                    # this fees is charged monthly
                    print('%s is monthly fees' % h)
                    due_this_term += amt

                if int(freq) == 3:
                    # this fee is charged quarterly
                    print('%s is quarterly fees' % h)
                    due_this_term += amt
                head[h] = amt
                heads_array.append(head)
            head = {}
            head['Due This term'] = due_this_term
            heads_array.append(head)
            head = {}

            # get the previous outstanding, if any
            due_amount = 0.0
            try:
                outstanding = PreviousBalance.objects.get(student=student)
                if outstanding.negative:
                    due_amount = outstanding.due_amount
                    print('%s has negative outstanding of %f' % (student, due_amount))
                    head['negative_outstanding'] = True
                else:
                    # advance payment is done
                    due_amount = 0.0 - outstanding.due_amount
                    print('%s has positive outstanding of %f' % (student, due_amount))
                    head['negative_outstanding'] = False

            except Exception as e:
                print('exception 21032019-C from erp views.py %s %s' % (e.message, type(e)))
                print('No Previous outstanding on %s' % student)
            head['Previous Outstanding'] = due_amount
            heads_array.append(head)
            head = {}

            # calculate how much has been paid till date
            payment_history = []
            entry = {}
            paid_till_date = 0.0
            try:
                payments = FeePaymentHistory.objects.filter(student=student)
                for payment in payments:
                    entry['date'] = payment.date
                    entry['amount'] = payment.amount
                    paid_till_date += payment.amount
                    entry['mode'] = payment.mode
                    entry['comments'] = payment.comment
                    payment_history.append(entry)
                    entry = {}
            except Exception as e:
                print('exception 21032019-B from erp views.py %s %s' % (e.message, type(e)))
                print('no payment history could be retrieved for %s of %s %s' %
                      (student, current_class, school))
            context_dict['payment_history'] = payment_history
            head['Paid Till date'] = paid_till_date

            heads_array.append(head)

            # check if there is a delay in paying fee
            if fee_frequency == 1:
                # monthly fees system. due date should be this month
                due_date = datetime(year=year, month=currentMonth, day=int(d_date))
            if fee_frequency == 3:
                if currentMonth in q1:
                    due_date = datetime(year=year, month=4, day=int(d_date))
                if currentMonth in q2:
                    due_date = datetime(year=year, month=7, day=int(d_date))
                if currentMonth in q3:
                    due_date = datetime(year=year, month=10, day=int(d_date))
                if currentMonth in q4:
                    due_date = datetime(year=year, month=1, day=int(d_date))

                print('due_date = ')
                print(due_date)
            # delay in days
            today = datetime.now()
            difference = (today - due_date).days
            print('delay by %i days' % difference)
            head = {}
            head['Days Delay'] = difference
            heads_array.append(head)

            # delay in weeks
            head = {}
            weeks = round(float(difference)/7.0, 1)
            print('delay by %.1f weeks' % weeks)
            head['Weeks Delay'] = weeks
            heads_array.append(head)

            context_dict['heads'] = heads_array

            os.remove(local_path)
            print(context_dict)
            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('exception 04032019-A from erp views.py %s %s' % (e.message, type(e)))
            print('failed in determining details regarding fees payment')
