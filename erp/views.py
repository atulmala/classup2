import os
import xlrd
import json
import inflect
import StringIO
import xlsxwriter

from google.cloud import storage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.renderers import JSONRenderer
from datetime import datetime
from dateutil import relativedelta

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import generics

from setup.forms import ExcelFileUploadForm
from setup.views import validate_excel_extension

from setup.models import School
from student.models import Student, AdditionalDetails, House, Parent
from exam.models import StreamMapping
from .models import CollectAdmFee, FeePaymentHistory, PreviousBalance, ReceiptNumber, HeadWiseFee, FeeCorrection

from .serializers import FeeHistorySerialzer


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


class FeeHistory(generics.ListAPIView):
    serializer_class = FeeHistorySerialzer

    def get_queryset(self):
        context_dict = {

        }
        try:
            school_id = self.request.GET.get('school_id')
            school = School.objects.get(id=school_id)
            print('school = %s' % school)
            reg_no = self.request.GET.get('reg_no')
            print('reg_no/erp_id = %s' % reg_no)
            student = Student.objects.get(school=school, student_erp_id=reg_no)
            print('getting fee history for %s of %s' % (student, school))

            q = FeePaymentHistory.objects.filter(student=student)
            print(q)
            return q
        except Exception as e:
            print('exception 11042019-A from erp views.py %s %s' % (e.message, type(e)))
            print('error while fetching fee payment history')
            context_dict['message'] = 'error'
            print(context_dict)
            return JSONResponse(context_dict, status=201)


class DefaulterReport(generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        school_name = school.school_name

        higher_classes = ['XI', 'XII']
        # get the fee detail excel sheet
        storage_client = storage.Client()
        bucket = storage_client.get_bucket('classup')
        print(bucket)
        fee_file = '%s.xlsx' % str(school_id)
        fee_file_path = 'classup2/Fee/%s/%s' % (str(school_id), fee_file)
        blob = bucket.blob(fee_file_path)
        local_path = 'erp/%s' % fee_file
        blob.download_to_filename(local_path)
        wb = xlrd.open_workbook(local_path)


        excel_file_name = 'Fee_Defaulter_List.xlsx'
        print (excel_file_name)
        output = StringIO.StringIO(excel_file_name)
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Defaulters')

        header = workbook.add_format({
            'bold': True,
            'bg_color': '#F7F7F7',
            'color': 'black',
            'align': 'center',
            'valign': 'top',
            'border': 1
        })
        title = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })

        money = workbook.add_format({
            'num_format':'#,##,##0.00',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1
        })
        money.set_border()

        cell_normal = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True
        })
        cell_normal.set_border()
        fail_format = workbook.add_format()
        fail_format.set_bg_color('yellow')

        excess_format = workbook.add_format()
        excess_format.set_bg_color('green')

        row = 0
        col = 0

        currentDay = datetime.now().day
        year = datetime.now().year
        month = datetime.now().month
        date = '%i/%i/%i' % (currentDay, month, year)
        sheet.merge_range(row, col, row, col + 7, '%s - Defaulter list as on %s' % (school_name, date), title)

        sheet.set_column('B:D', 20)
        sheet.set_column('E:H', 12)
        row += 1
        col = 0
        sheet.write_string(row, col, 'S No.', header)
        col += 1
        sheet.write_string(row, col, 'Parent', header)
        col += 1
        sheet.write_string(row, col, 'Mobile No', header)
        col += 1
        sheet.write_string(row, col, 'Student', header)
        col += 1
        sheet.write_string(row, col, 'Adm. No', header)
        col += 1
        sheet.write_string(row, col, 'Class', header)
        col += 1
        sheet.write_string(row, col, 'Amount Due till date', header)
        col += 1
        sheet.write_string(row, col, 'Paid till date', header)
        col += 1
        sheet.write_string(row, col, 'Net Amount Due', header)
        col += 1
        sheet.write_string(row, col, 'Family Due', header)

        row += 1
        col = 0
        parents = Student.objects.filter(school=school).order_by('parent').values('parent').distinct()
        print(parents)

        try:
            # how many months have passed since the sessio start
            first_april = datetime(2019, 4, 1)
            today = datetime.today()
            diff = relativedelta.relativedelta(today, first_april)
            months_count = diff.months

            parents = Student.objects.filter(school=school).order_by('parent').values('parent').distinct()
            print(parents)
            index = 1
            grand_total = 0.00
            for parent in parents:
                pk = parent['parent']
                the_parent = Parent.objects.get(pk=pk)
                print(the_parent)
                entry = Student.objects.filter(school=school, parent=the_parent)
                print(entry)
                family_total = 0.0
                for student in entry:
                    print('now dealing with %s ward of %s' % (student, the_parent))
                    due_this_term = 0.0
                    due_till_now = 0.0


                    # 02/04/2019 - the outstanding will be calcualted as follows: we will determine the fee due till date
                    # for example if today is 7th of Jul and fee payment is monthly we will calculate the fee
                    # due by addidng monthly fee for april, may, june and july.
                    # then we will add any outstanding (means and shortfall in fee paid last time)
                    # we then calculate how much has been paid for this student till now
                    # due on student = fee due till date + outstanding - fee paid till date
                    if student.current_class.standard in higher_classes:
                        print('%s is in higher class %s. Fee will be calculated as per chosen stream' %
                              (student, student.current_class.standard))
                        try:
                            mapping = StreamMapping.objects.get(student=student)
                            stream = mapping.stream.stream
                            print('stream chosen by %s is %s' % (student, stream))
                            current_class = '%s-%s' % (student.current_class.standard, stream)
                        except Exception as e:
                            print('failed to determine stream for %s' % student)
                            print('exception 10062019-A from erp views.py %s %s' % (e.message, type(e)))
                    else:
                        current_class = student.current_class.standard
                    input_sheet = wb.sheet_by_name(current_class)
                    for sheet_row in range(input_sheet.nrows):
                        if sheet_row == 0:
                            fee_frequency = input_sheet.cell(sheet_row, 1).value
                            d_date = input_sheet.cell(sheet_row, 3).value
                            continue
                        if sheet_row == 1:
                            continue
                        head = {}
                        h = input_sheet.cell(sheet_row, 0).value
                        amt = input_sheet.cell(sheet_row, 1).value
                        freq = input_sheet.cell(sheet_row, 2).value

                        if int(freq) == 0:
                            # this is one time fee (admission/caution). check if this fee to be charged for this student
                            print('%s is one time fees. checking whether it has been paid or not' % h)
                            try:
                                c = CollectAdmFee.objects.get(student=student)
                                print('%s has NOT paid one time fees %s' % (student, h))
                                due_this_term += amt
                                due_till_now += amt
                            except Exception as e:
                                print('exception 21032019-A from erp views.py %s %s' % (e.message, type(e)))
                                print('%s has paid one time fees %s' % (student, h))
                                amt = 'N/A'

                        if int(freq) == 12:
                            due_till_now += amt
                            # this is once in a year fee like annual fee, exam fee etc. this is to be charge in April
                            print('%s is annual fees to be charged in the month of april' % h)
                            print('and the month is %s' % month)
                            if month == 4:
                                head['amount'] = amt
                                due_this_term += amt
                            else:
                                amt = 'N/A'

                        if int(freq) == 1:
                            # this fees is charged monthly
                            print('%s is monthly fees' % h)
                            due_this_term += amt

                            # how much of this fee is accumulated till now
                            due_till_now += amt * months_count

                        if int(freq) == 3:
                            # this fee is charged quarterly
                            print('%s is quarterly fees' % h)
                            due_this_term += amt

                            # how much of this fee is accumulated till now
                            due_till_now += amt * (months_count / 3)
                    # get the outstanding on this student
                    outstanding = 0.0
                    try:
                        pb = PreviousBalance.objects.get(school=school, student=student)
                        outstanding = pb.due_amount
                    except Exception as e:
                        print('exception 02042019-A from erp views.py %s %s' % (e.message, type(e)))
                        print('%s has no previous outstanding' % student)

                    # check how much has been paid till date
                    history = FeePaymentHistory.objects.filter(student=student).aggregate(Sum('amount'))
                    paid_till_date = history['amount__sum']
                    if paid_till_date == None:
                        paid_till_date = 0.0

                    # now the net due
                    print('due_till_now = %.2f' % due_till_now)
                    print('due_this_term = %.2f' % due_this_term)
                    print('outstanding = %.2f' %  outstanding)


                    print('paid_till_date = %.2f' % paid_till_date)

                    net_due = float(due_till_now) + float(due_this_term) + float(outstanding) - float(paid_till_date)
                    print('net due = %.2f' % net_due)
                    if net_due > 0.0:
                        sheet.write_number(row, col, index, cell_normal)
                        index += 1
                        col += 1
                        sheet.write_string(row, col, student.parent.parent_name, cell_normal)
                        col += 1
                        sheet.write_string(row, col, student.parent.parent_mobile1, cell_normal)
                        col += 1
                        sheet.write_string(row, col, '%s %s' % (student.fist_name, student.last_name), cell_normal)
                        col += 1
                        sheet.write_string(row, col, '%s' % student.student_erp_id, cell_normal)
                        col += 1
                        sheet.write_string(row, col, '%s-%s' %
                                           (student.current_class.standard,
                                            student.current_section.section), cell_normal)
                        col += 1
                        sheet.write_number(row, col, due_till_now + due_this_term + outstanding, money)
                        col += 1
                        sheet.write_number(row, col, paid_till_date, money)
                        col += 1
                        sheet.write_number(row, col, net_due, money)
                        grand_total += float(net_due)
                        col += 1
                        family_total += float(net_due)
                        print('family total = %.2f' % family_total)
                        sheet.write_number(row, col, family_total, money)

                    row += 1
                    col = 0
                # check if this parent has multiple kids
                if entry.count() > 1:
                    if net_due > 0.0:
                        f_row = row - entry.count()
                        sheet.conditional_format(f_row, 0, row - 1, col + 9, {'type': 'no_blanks', 'format': fail_format})
                        sheet.merge_range(f_row, col + 9, row - 1, col + 9, str(family_total), money)
                        sheet.merge_range(f_row, col + 1, row - 1, col + 1, the_parent.parent_name, cell_normal)
                        sheet.merge_range(f_row, col + 2, row - 1, col + 2, the_parent.parent_mobile1, cell_normal)
                    else:
                        row -= entry.count()

            sheet.write_string(row, col + 5, 'Grand Total', title)
            sheet.write_number(row, col + 6, grand_total, money)

            # close the workbook
            print('about to close the workbook')
            workbook.close()
            print('workbook closed')

            # remove the fee detail sheet from local storage
            os.remove(local_path)

            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=' + excel_file_name
            response.write(output.getvalue())
            return response

        except Exception as e:
            print('exception 30032109-A from erp views.py %s %s' % (e.message, type(e)))
            print('failed to execute query')
            context_dict = {}
            context_dict['status'] = 'failed'
            context_dict['message'] = 'Failed to create defaulter list. Please contact ClassUp Support'
            return JSONResponse(context_dict, status=201)


class CorrectFee(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        try:
            data = json.loads(request.body)
            print(data)
            school_id = self.kwargs['school_id']
            school = School.objects.get(pk=school_id)
            receipt_corrected = data['receipt_corrected']
            penalty = data['penalty']
            one_time = data['one_time']
            discount = data['discount']
            amount_paid = data['amount_paid']

            try:
                # first, carry out the correction in Fee payment history
                correction = FeePaymentHistory.objects.get(school=school, receipt_number = receipt_corrected)
                data = correction.data
                print('json data in string = %s' % data)
                the_json = json.loads(data)
                the_json['']
                correction.fine = penalty
                correction.one_time = one_time
                correction.discount = discount
                correction.amount = amount_paid
                correction.save()
                print('correction successfully carried out for receipt # %i of %s' % (receipt_corrected, school))

                # then, save in the correction table (for the purpose of audit trail
                correction2 = FeeCorrection(school=school, receipt_number=receipt_corrected, amount=amount_paid,
                                            fine=penalty, discount=discount)
                correction2.save()

                context_dict['outcome'] = 'success'
                return JSONResponse(context_dict, status=200)
            except Exception as e:
                print('failed to carry out fee correction for receipt no %i of %s' % (receipt_corrected, school))
                print('exception 190519-A from erp views.py %s %s' % (e.message, type(e)))
                context_dict['outcome'] = 'failure'
                return JSONResponse(context_dict, status=201)
        except Exception as e:
            print('failed to carry out fee correction')
            print('exception 190519-B from erp views.py %s %s' % (e.message, type(e)))
            context_dict['outcome'] = 'failure'
            return JSONResponse(context_dict, status=201)


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
            h = json.dumps(heads)
            print('type h = %s' % type(h))
            print('h = %s' % h)
            print('heads type = %s' % type(heads))
            print('heads = ')
            print(heads)
            due_this_term = data['due_this_term']
            actual_paid = data['actual_paid']
            previous_dues = data['previous_due']
            print('previous dues = %.2f' % previous_dues)
            one_time = data['one_time']
            print('one_time = %.2f' % float(one_time))

            fine = data['fine']
            print('late fee = %.2f' % float(fine))
            waiver = data['waiver']
            print('waiver = %.2f' % float(waiver))
            discount = data['discount']
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
                                    one_time=one_time, discount=discount, waiver=waiver, mode=mode,
                                    cheque_number=cheque_no, bank=bank, comments='No comments',
                                    receipt_number=receipt_no)
            try:
                fee.data = str(h)
                fee.save()
            except Exception as e:
                print('exception 11052019-A from erp views.py %s %s' % (e.message, type(e)))
                print('failed to save heads')
            fee.save()

            # if one time fee such as admission fee was taken set whether_paid to true
            try:
                c = CollectAdmFee.objects.get(student=student)
                c.whehter_paid = True
                print('%s of %s has paid admission fee' % (student, school))
            except Exception as e:
                print('exception 31032019-B from erp views.py %s %s' % (e.message, type(e)))
                print('One time fee was not charged from %s of %s' % (student, school))

            # save head-wise fee
            for head in heads:
                h = head['head']
                amount = head['amount']
                if amount != 'N/A':
                    net_paid = head['net_payable']
                    entry = HeadWiseFee(PaymentHistory=fee, school=school,
                                        student=student, head=h, amount=float(net_paid))
                    entry.save()

            # also save late fee, one_time and discount as heads. Only if they are actually charged or provided
            if fine > 0.0:
                late_fee = HeadWiseFee(PaymentHistory=fee, school=school,
                                       student=student, head='Fine', amount=float(fine))
                late_fee.save()

            if waiver > 0.0:
                w = HeadWiseFee(PaymentHistory=fee, school=school,
                                     student=student, head='Waiver', amount=float(waiver))
                w.save()

            if discount > 0.0:
                disc = HeadWiseFee(FeePaymentHistory=fee, school=school,
                                   student=student, head='Discount', amount=float(discount))
                disc.save()

            if one_time > 0.0:
                ot = HeadWiseFee(PaymentHistory=fee, school=school, student=student, head='One Time',
                                 amount=float(one_time))
                ot.save()

            # adjust the balance. We will be storing only the balance which is to be collected in future. Sometimes
            # parents pay excess fee. That is not to be stored as it will be the amount_paid and automatically take
            # care of itself at the time of next fee deposit
            try:
                pending = PreviousBalance.objects.get(student=student)
                if pending.due_amount != 0.0:
                    if balance > 0.0:
                        pending.due_amount = balance
                        pending.save()
                if pending.due_amount == 0.0:
                    pending.delete()
            except Exception as e:
                print('exception 24032019-B from erp views.py %s %s' % (e.message, type(e)))
                print('%s of %s has no previous balance.' % (student, school))
                if balance != 0.0 or balance != 0.00:
                    if balance > 0.0:
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
            print('top position before drawing fee head table = %i' % top_position)

            # show fee heads inside table
            data1 = [['Fee Head                       ', 'Amount  ', 'Disc. (%)', 'Disc. Amt', 'Net Payable']]
            style4 = [('GRID', (0, 0), (-1, -1), 0.5, colors.black), ('TOPPADDING', (0, 0), (-1, -1), 1),
                      ('BOTTOMPADDING', (0, 0), (-1, -1), 1), ('FONT', (0, 0), (4, 0), 'Times-Bold'),
                      ('FONTSIZE', (0, 0), (-1, -1), 10)]
            total_discount = 0.0
            for head in heads:
                amount = head['amount']
                discount_perc = '%s %%' % str(head['discount_perc'])
                discount_amt = head['discount_amt']
                total_discount += discount_amt
                net_paid = head['net_payable']
                data1.append([head['head'], amount, discount_perc, discount_amt, net_paid])
            fee.discount = total_discount
            fee.save()

            head_count = len(heads)
            top_position -= 18 * head_count + 15
            print('top  position = %i' % top_position)
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
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(previous_dues))
            c.drawString(amt_pos2, top_position, str(previous_dues))

            top_position -= 15
            text = 'C. Late Fee/Fine: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(fine))
            c.drawString(amt_pos2, top_position, str(fine))

            top_position -= 15
            text = 'D. One time Charges: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(one_time))
            c.drawString(amt_pos2, top_position, str(one_time))

            top_position -= 15
            text = 'E. Waiver: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(waiver))
            c.drawString(amt_pos2, top_position, str(waiver))

            top_position -= 15
            text = 'F. Net Payable (A + B + C + D - E): '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(net_payable))
            c.drawString(amt_pos2, top_position, str(net_payable))

            top_position -= 20
            c.setFont('Times-Bold', 14)
            text = 'G. Actual Paid: '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            c.drawString(amt_pos1, top_position, str(actual_paid))
            c.drawString(amt_pos2, top_position, str(actual_paid))

            top_position -= 20
            c.setFont(font, 10)
            text = 'H. Balance (F - G): '
            c.drawString(r1_border, top_position, text)
            c.drawString(r2_border, top_position, text)
            if balance < 0.0:
                balance = abs(balance)
                c.drawString(amt_pos1, top_position, '%s (Positive)' % str(balance))
                c.drawString(amt_pos2, top_position, '%s (Positive)' % str(balance))
            else:
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
        q1 = [4, 5, 6]
        q2 = [7, 8, 9]
        q3 = [10, 11, 12]
        q4 = [1, 2, 3]

        higher_classes = ['XI', 'XII']

        try:
            school_id = request.GET.get('school_id')
            school = School.objects.get(pk=school_id)

            student_id = request.GET.get('student_id')
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

            if current_class in higher_classes:
                print('%s is in higher class. Fee will be calculated as per chosen stream' % student)
                try:
                    mapping = StreamMapping.objects.get(student=student)
                    stream = mapping.stream.stream
                    print('stream chosen by %s is %s' % (student, stream))
                    current_class = '%s-%s' % (current_class, stream)
                except Exception as e:
                    print('failed to determine stream for %s' % student)
                    print('exception 09062019-A from erp views.py %s %s' % (e.message, type(e)))
            fee_file = '%s.xlsx' % str(school_id)
            fee_file_path = 'classup2/Fee/%s/%s' % (str(school_id), fee_file)
            blob = bucket.blob(fee_file_path)
            local_path = 'erp/%s' % fee_file
            blob.download_to_filename(local_path)
            wb = xlrd.open_workbook(local_path)
            sheet = wb.sheet_by_name(current_class)
            heads_array = []

            session_begins = 4
            start_date = datetime(2019, session_begins, 1)
            today = datetime.today()
            diff = relativedelta.relativedelta(today, start_date)
            months_count = diff.months

            due_this_term = 0.0
            due_till_now = 0.0
            for row in range(sheet.nrows):
                if row == 0:
                    fee_frequency = sheet.cell(row, 1).value
                    d_date = int(sheet.cell(row, 3).value)
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
                        c = CollectAdmFee.objects.get(student=student)
                        if not c.whehter_paid:
                            print('%s has NOT paid one time fees %s' % (student, h))
                            due_this_term += amt
                            #due_till_now += amt
                        else:
                            print('%s has already paid one time fees %s' % (student, h))
                            due_till_now += amt
                    except Exception as e:
                        print('exception 21032019-A from erp views.py %s %s' % (e.message, type(e)))
                        print('%s has paid one time fees %s' % (student, h))
                        amt = 'N/A'

                if int(freq) == 12:
                    # this is once in a year fee like annual fee, exam fee etc. this is to be charge in April
                    print('%s is annual fees to be charged in the month of april' % h)
                    print('and the month is %s' % month)
                    if month == session_begins:
                        due_this_term += amt
                    else:
                        due_till_now += amt
                        amt = 'N/A'

                if int(freq) == 1:
                    # this fees is charged monthly
                    print('%s is monthly fees' % h)
                    due_this_term += amt

                    # how much of this fee is accumulated till now
                    due_till_now += amt * months_count

                if int(freq) == 3:
                    # this fee is charged quarterly
                    print('%s is quarterly fees' % h)
                    due_this_term += amt

                    # how much of this fee is accumulated till now
                    due_till_now += amt * (months_count/3)
                head['head'] = h
                head['amount'] = amt
                heads_array.append(head)
            head = {}
            context_dict['Due this term'] = due_this_term
            context_dict['Due till now'] = due_till_now

            # get the previous outstanding, if any
            due_amount = 0.0
            try:
                outstanding = PreviousBalance.objects.get(student=student)
                if outstanding.negative:
                    if months_count > 0:
                        due_amount = outstanding.due_amount
                        print('%s has negative outstanding of %f' % (student, due_amount))
                        head['negative_outstanding'] = True
                    else:
                        due_amount = 0.0
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
                    paid_till_date += float(payment.amount)
                    entry['mode'] = payment.mode
                    entry['comments'] = payment.comments
                    payment_history.append(entry)
                    entry = {}
            except Exception as e:
                print('exception 21032019-B from erp views.py %s %s' % (e.message, type(e)))
                print('no payment history could be retrieved for %s of %s %s' %
                      (student, current_class, school))
            context_dict['payment_history'] = payment_history
            context_dict['Paid till date'] = paid_till_date
            print(context_dict)

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

            # delay in weeks
            weeks = round(float(difference) / 7.0, 1)
            print('delay by %.1f weeks' % weeks)

            if difference > 1:
                context_dict['Days Delay'] = difference
                context_dict['Weeks Delay'] = weeks
            else:
                context_dict['Days Delay'] = 'No Delay'
                context_dict['Weeks Delay'] = 'No Delay'
            context_dict['heads'] = heads_array

            os.remove(local_path)
            print(context_dict)
            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('exception 04032019-A from erp views.py %s %s' % (e.message, type(e)))
            print('failed in determining details regarding fees payment')


from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser
@parser_classes((MultiPartParser, ))
class UploadFee(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, format=None):
        print('resuest = ')
        print(request.FILES)
        context_dict = {

        }

        try:
            print ('now starting to process the uploaded file for fee upload...')
            fileToProcess_handle = request.FILES['fee_deposit_detail.xlsx']

            # check that the file uploaded should be a valid excel
            # file with .xls or .xlsx

            # if this is a valid excel file - start processing it
            fileToProcess = xlrd.open_workbook(filename=None, file_contents=fileToProcess_handle.read())
            sheet = fileToProcess.sheet_by_index(0)
            if sheet:
                print ('Successfully got hold of sheet!')
            for row in range(sheet.nrows):
                # first two rows are header rows
                if row == 0:
                    school_id = sheet.cell(row, 0).value
                    school = School.objects.get(pk=school_id)
                    print('school = %s' % school)
                    continue
                print ('Processing a new row')
                try:
                    erp_id = str(sheet.cell(row, 1).value)
                    decimal = '.'
                    if decimal in erp_id:
                        print('student id contains a decimal followed by zero. This has to be removed')
                        erp_id = erp_id[:-2]
                        print('decimal and following zero removed. Now student_id = %s' % erp_id)
                except Exception as e:
                    print('exception 13062019-A from erp views. %s %s' % (e.message, type(e)))

                try:
                    student = Student.objects.get(school=school, student_erp_id=erp_id)

                    print('updating the fee paid by %s with erp_id %s' % (student, erp_id))
                    data = {

                    }
                    try:
                        tuition_fee = sheet.cell(row, 3).value
                        data['Tuition Fee'] = tuition_fee
                        transport_fee = sheet.cell(row, 4).value
                        data['Transportation Fee'] = transport_fee
                        admission_fee = sheet.cell(row, 5).value
                        data['Admission Fee'] = admission_fee
                        excess_payment = sheet.cell(row, 6).value
                        data['Excess Payment'] = excess_payment
                        amount_paid = sheet.cell(row, 7).value
                        receipt_no = sheet.cell(row, 8).value

                        fee_history = FeePaymentHistory(school=school, student=student, data=data,
                                                        amount=amount_paid, mode='cash', receipt_number=receipt_no)
                        fee_history.save()
                        print('updated fee details for student %s with erp id %s'
                              % (erp_id, student))
                    except Exception as e:
                        print('exception 13062019-B from erp views.py %s %s' % (e.message, type(e)))
                        print('failed to update fee details for %s with erp_id %s' %
                              (student, erp_id))

                    # if one time fee such as admission fee was taken set whether_paid to true
                    if excess_payment > 0.0:
                        try:
                            c = CollectAdmFee(school=school, student=student, whether_paid=True)
                            c.save()
                            print('%s of %s has paid admission fee' % (student, school))
                        except Exception as e:
                            print('exception 13062019-DB from erp views.py %s %s' % (e.message, type(e)))
                            print('failed to enter one time Collectadmin fee from %s of %s' % (student, school))

                    # save head-wise fee
                    print('now store head wise fee for %s with erp_id %s' % (student, erp_id))
                    for head, amount in data.items():
                        print('head = %s, amount = %f' % (head, amount))
                        if amount > 0.0:
                            try:
                                entry = HeadWiseFee(PaymentHistory=fee_history, school=school,
                                                    student=student, head=head, amount=float(amount))
                                entry.save()
                            except Exception as e:
                                print('exception 13062019-E from erp views.py %sw %s' % (e.message, type(e)))
                                print('failed to save a head component for %s' % student)
                except Exception as e:
                    print('exception 13062019-F from erp views.py %s %s' % (e.message, type(e)))
                    print('no student associated with erp_id %s' % erp_id)
                row += 1
                # file upload and saving to db was successful. Hence go back to the main menu
            messages.success(request._request, 'Additional Details Successfully uploaded')
            return render(request, 'classup/setup_index.html', context_dict)
        except Exception as e:
            error = 'invalid excel file uploaded.'
            print (error)
            print ('exception 19032018-D from erp views.py %s %s ' % (e.message, type(e)))
            return render(request, 'classup/setup_data.html', context_dict)


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
                        erp_id = str(sheet.cell(row, 1).value)
                        decimal = '.'
                        if decimal in erp_id:
                            print('student id contains a decimal followed by zero. This has to be removed')
                            erp_id = erp_id[:-2]
                            print('decimal and following zero removed. Now student_id = %s' % erp_id)
                        mother_name = (sheet.cell(row, 4).value).title()
                        address = sheet.cell(row, 5).value
                        house = (sheet.cell(row, 6).value).title()
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
                            try:
                                ad = AdditionalDetails(student=student, mother_name=mother_name, address=address)
                                ad.save()
                                print('successfully created additional details for %s with erp_id %s' %
                                      (student_name, erp_id))
                            except Exception as e:
                                print('exception 30052019-A from erp views.py %s %s' % (e.message, type(e)))
                                print('failed to set up additional details for %s' % student)

                        print('now setting the house details for %s with erp_id %s' % (student_name, erp_id))
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
