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
