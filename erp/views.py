import os
import xlrd
import json
import inflect

from google.cloud import storage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle


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
from .models import CollectAdmFee, FeePaymentHistory, PreviousBalance, ReceiptNumber

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


class ProcessFee(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        try:
            data = json.loads(request.body)
            print(data)
            school_id = self.kwargs['school_id']
            school = School.objects.get(pk=school_id)
            student_id = data['reg_no']
            student = Student.objects.get(school=school, student_erp_id=student_id)
            print('processing fee for %s of %s' % (student, school))
            heads = data['heads']
            print('heads = ')
            print(heads)
            due_this_term = data['due_this_term']
            actual_paid = data['actual_paid']
            previous_dues = data['previous_due']
            print('previous dues = %.2f' % previous_dues)
            fine = data['fine']
            print('late fee = %.2f' % float(fine))
            discount = data['discount']
            print('discount = %.2f' % float(discount))
            net_payable = data['net_payable']
            balance = data['balance']
            mode = data['mode']
            print('payment_mode = %s' % mode)
            cheque_no = data['cheque_no']
            print('cheque no = %s' % cheque_no)
            bank = data['bank']
            print('bank = %s' % bank)

            # generate receipt number
            try:
                r = ReceiptNumber.objects.get(school=school)
                receipt_no = r.start_receipt
                r.start_receipt = receipt_no + 1
                r.save()
            except Exception as e:
                receipt_no = 99999

            fee = FeePaymentHistory(school=school, student=student, amount=actual_paid, fine=fine,
                                    discount=discount, mode=mode, cheque_number=cheque_no,
                                    bank=bank, comments='No comments', receipt_number=receipt_no)
            fee.save()

            # adjust the balance
            try:
                pending = PreviousBalance.objects.get(student=student)
                if pending.due_amount != 0.0:
                    pending.due_amount = balance
                    pending.save()
            except Exception as e:
                print('exception 24032019-B from erp views.py %s %s' % (e.message, type(e)))
                print('%s of %s has no previous balance.' % (student, school))
                pending = PreviousBalance(student=student, school=school)
                pending.due_amount = balance
                pending.save()
            print('%s of %s has now a new balance of %.2f' % (student, school, balance))

            # prepare the receipt in pdf
            pdf_name = '%s_%s_(%s)_fee_receipt.pdf' % (student.fist_name,
                                                       student.last_name, student.student_erp_id)
            print('pdf will be generated with name %s' % pdf_name)
            response = HttpResponse(content_type='application/pdf')
            content_disposition = ('attachment; filename= %s' % pdf_name)
            print (content_disposition)
            response['Content-Disposition'] = content_disposition
            c = canvas.Canvas(response, pagesize=landscape(A4), bottomup=1)
            c.translate(inch, inch)
            font = 'Times-Bold'
            font_size = 14
            c.setFont(font, font_size)
            top = 450
            line_top = top - 10
            c.drawString(30, top + 20, school.school_name)
            c.drawString(480, top + 20, school.school_name)
            c.setFont(font, 10)
            c.drawString(480, top + 7, school.school_address)
            c.drawString(30, top + 7, school.school_address)

            c.drawString(95, top - 25, 'Fee Receipt')
            c.drawString(530, top - 25, 'Fee Receipt')
            c.setFont(font, 8)
            c.setFont(font, 10)
            r1_border = -30
            r2_border = 400
            c.line(-30, line_top, 300, line_top)
            c.line(400, line_top, 730, line_top)

            currentDay = datetime.now().day
            year = datetime.now().year
            month = datetime.now().month
            transaction_date = '%i/%i/%i' % (currentDay, month, year)
            top_position = top - 40
            c.drawString(-30, top_position, 'Date: ')
            c.drawString(10, top_position, transaction_date)
            c.drawString(400, top_position, 'Date: ')
            c.drawString(440, top_position, transaction_date)

            c.drawString(200, top_position, 'Receipt #: ')
            c.drawString(250, top_position, str(receipt_no))
            c.drawString(630, top_position, 'Receipt #: ')
            c.drawString(680, top_position, str(receipt_no))

            top_position -= 15
            c.drawString(-30, top_position, 'Student Name: ')
            c.drawString(40, top_position, '%s %s' % (student.fist_name, student.last_name))
            c.drawString(400, top_position, 'Student Name: ')
            c.drawString(470, top_position, '%s %s' % (student.fist_name, student.last_name))
            c.drawString(200, top_position, 'Reg/Adm No: ')
            c.drawString(260, top_position, student.student_erp_id)
            c.drawString(630, top_position, 'Reg/Adm No: ')
            c.drawString(690, top_position, student.student_erp_id)

            top_position -= 15
            c.drawString(-30, top_position, 'Class: ')
            c.drawString(5, top_position, '%s-%s' %
                         (student.current_class.standard, student.current_section.section))
            c.drawString(400, top_position, 'Class: ')
            c.drawString(430, top_position,
                         '%s-%s' % (student.current_class.standard, student.current_section.section))

            top_position -= 15
            c.drawString(-30, top_position, 'Parent Name: ')
            c.drawString(40, top_position, student.parent.parent_name)
            c.drawString(400, top_position, 'Parent Name: ')
            c.drawString(470, top_position, student.parent.parent_name)
            c.drawString(200, top_position, 'Mob: ')
            c.drawString(230, top_position, student.parent.parent_mobile1)
            c.drawString(630, top_position, 'Mob: ')
            c.drawString(660, top_position, student.parent.parent_mobile1)

            # show fee heads inside table
            data1 = [['Fee Head                                                            ', 'Amount       ']]
            style4 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black), ('TOPPADDING', (0, 0), (-1, -1), 1),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 1), ('FONT', (0, 0), (1, 0), 'Times-Bold'),
                      ('FONTSIZE', (0, 0), (-1, -1), 10)]
            for head in heads:
                amount = head['amount']
                data1.append([head['head'], amount])
            top_position -= 110
            table = Table(data1)
            table.setStyle(TableStyle(style4))

            table.wrapOn(c, -30, 0)
            table.drawOn(c, -30, top_position)
            table.drawOn(c, 400, top_position)

            amt_pos1 = 160
            amt_pos2 = 600
            top_position -= 25
            text = 'A. Charges for this Month/Qtr: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(due_this_term))
            c.drawString(amt_pos2, top_position, str(due_this_term))

            top_position -= 15
            text = 'B. Previous Dues: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border,top_position, text)
            c.drawString(amt_pos1, top_position, str(previous_dues))
            c.drawString(amt_pos2, top_position, str(previous_dues))

            top_position -= 15
            text = 'C. Late Fee/Fine: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(fine))
            c.drawString(amt_pos2, top_position, str(fine))

            top_position -= 15
            text = 'D. Discount/Waiver: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(discount))
            c.drawString(amt_pos2, top_position, str(discount))

            top_position -= 15
            text = 'E. Net Payable (A + B + C - D): '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(net_payable))
            c.drawString(amt_pos2, top_position, str(net_payable))

            top_position -= 20
            c.setFont('Times-Bold', 14)
            text = 'F. Actual Paid: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(actual_paid))
            c.drawString(amt_pos2, top_position, str(actual_paid))

            top_position -= 20
            c.setFont(font, 10)
            text = 'G. Balance (F - E): '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(balance))
            c.drawString(amt_pos2, top_position, str(balance))

            top_position -= 20
            text = 'Mode: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, mode)
            c.drawString(amt_pos2, top_position, mode)

            if mode == 'cheque':
                top_position -= 20
                text = 'Cheque No / Bank : '
                c.drawString(r1_border, top_position, text)
                c.drawString(r2_border, top_position, text)
                c.drawString(amt_pos1, top_position, '%s / %s' % (cheque_no, bank))
                c.drawString(amt_pos2, top_position, '%s / %s' % (cheque_no, bank))
                top_position -= 10
                c.setFont(font, 7)
                c.drawString(r1_border, top_position, '(Subject to realisation)')
                c.drawString(r2_border, top_position, '(Subject to realisation)')

            top_position -= 20
            c.setFont(font, 10)
            p = inflect.engine()
            in_words = p.number_to_words(actual_paid)
            text = 'Received a sum of Rupees %s.00 (%s) only' % (str(actual_paid), in_words)
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)

            top_position -= 60
            text = 'Cashier/Accountant Signature'
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)

            text = 'Recepient signature'
            c.drawString(r1_border + 200, top_position, text)
            c.drawString(r2_border + 200, top_position, text)

            top_position -= 50

            c.setFont(font, 7)
            c.drawString(r1_border + 150, top_position, 'School copy')
            c.drawString(r2_border + 150, top_position, 'Student copy')

            c.save()

            return response
        except Exception as e:
            print('exception 24032019-A from erp views.py %s %s ' % (e.message, type(e)))
            print('error while processing fee')
            context_dict['status'] = 'error'
            context_dict['message'] = 'error while processing fee'
            return JSONResponse(context_dict, status=201)


class FeeDetails(generics.ListCreateAPIView):
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
                head['head'] = h
                head['amount'] = amt
                heads_array.append(head)
            head = {}
            context_dict['Due this term'] =due_this_term

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
            context_dict['Previous Outstanding'] = due_amount

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
            context_dict['Paid till date'] = paid_till_date

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
            context_dict['Days Delay'] = difference
            # delay in weeks
            weeks = round(float(difference)/7.0, 1)
            print('delay by %.1f weeks' % weeks)
            context_dict['Weeks Delay'] = weeks

            context_dict['heads'] = heads_array

            os.remove(local_path)
            print(context_dict)
            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('exception 04032019-A from erp views.py %s %s' % (e.message, type(e)))
            print('failed in determining details regarding fees payment')



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


