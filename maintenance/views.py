import urllib
import json
import random

from django.db.models import Count, Max, Sum
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.renderers import JSONRenderer
from rest_framework import generics

from datetime import datetime, timedelta

from attendance.models import Attendance, DailyAttendanceSummary
from online_test.models import StudentTestAttempt, StudentQuestion
from operations.models import SMSRecord, ResendSMS, SMSBatch
from teacher.models import MessageReceivers
from setup.models import School
from student.models import Student

from .models import SMSDelStats, DailyMessageCount

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


class DeleteMessages(generics.ListCreateAPIView):
    def delete(self, request, *args, **kwargs):
        t1 = datetime.now()
        context_dict = {'start_time': '%s' % t1}
        # print ('start_time = %s' % t1)
        school_id = request.POST.get('school_id')
        school = School.objects.get(school_name='Radisson the School')

        messages = SMSRecord.objects.filter(school=school)
        total = messages.count()
        for message in messages:
            message.delete()
            print('message deleted')
            total -= 1
            print('remaining messages to be deleted = %i' % total)

        t2 = datetime.now()
        # print ('end_time = %s' % t2)
        context_dict['end_time'] = '%s' % t2
        time_taken = t2 - t1
        context_dict['time_taken'] = time_taken
        return JSONResponse(context_dict, status=200)


class ResendFailedMessages(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        t1 = datetime.now()
        context_dict = {'start_time': '%s' % t1}
        records = ResendSMS.objects.filter(status='Not Available')
        for record in records:
            print(record.sms_record.message)
            print()

        t2 = datetime.now()
        context_dict['end_time'] = '%s' % t2
        time_taken = t2 - t1
        context_dict['time_taken'] = time_taken
        return JSONResponse(context_dict, status=200)


class DeDup(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        try:
            unique_fields = ['student', 'online_test']
            print('try to identify duplicate entries for test attempts')
            duplicates = (
                StudentTestAttempt.objects.values(*unique_fields)
                    .order_by()
                    .annotate(max_id=Max('id'), count_id=Count('id'))
                    .filter(count_id__gt=1)
            )

            print('total %i duplicates online tests found' % len(duplicates))
            context_dict['duplicate online test'] = len(duplicates)

            for duplicate in duplicates:
                print(duplicate)
                (
                    StudentTestAttempt.objects
                        .filter(**{x: duplicate[x] for x in unique_fields})
                        .exclude(id=duplicate['max_id'])
                        .delete()
                )
            context_dict['remove_duplicate_test_attempts'] = 'success'
        except Exception as e:
            print('exception 04052020-A from maintenance views.py %s %s' % (e.message, type(e)))
            print('failed in removing duplicate test attempts')

        try:
            unique_fields = ['student', 'question']
            print('try to identify duplicate answers by student')
            duplicates = (
                StudentQuestion.objects.values(*unique_fields)
                    .order_by()
                    .annotate(max_id=Max('id'), count_id=Count('id'))
                    .filter(count_id__gt=1)
            )

            print('total %i duplicates answers found' % len(duplicates))
            context_dict['duplicate anwers'] = len(duplicates)

            for duplicate in duplicates:
                print(duplicate)
                (
                    StudentQuestion.objects
                        .filter(**{x: duplicate[x] for x in unique_fields})
                        .exclude(id=duplicate['max_id'])
                        .delete()
                )
            context_dict['remove_duplicate_answers'] = 'success'

        except Exception as e:
            print('exception 04052020-B from maintenance views.py %s %s' % (e.message, type(e)))
            print('failed in removing duplicate answers')

        try:
            unique_fields = ['date', 'the_class', 'section', 'subject', 'student', 'taken_by']
            print('try to identify duplicate entries for attendances')
            duplicates = (
                Attendance.objects.values(*unique_fields)
                    .order_by()
                    .annotate(max_id=Max('id'), count_id=Count('id'))
                    .filter(count_id__gt=1)
            )

            print('total %i duplicates attendances found' % len(duplicates))
            context_dict['duplicate attendances count'] = len(duplicates)

            for duplicate in duplicates:
                print(duplicate)
                (
                    Attendance.objects
                        .filter(**{x: duplicate[x] for x in unique_fields})
                        .exclude(id=duplicate['max_id'])
                        .delete()
                )
            context_dict['remove_dup_attendance'] = 'success'

            # 17/07/2019 - now remove duplicate attendance summaries
            unique_fields = ['date', 'the_class', 'section', 'subject', 'total', 'present', 'absent', 'percentage']
            print('try to identify duplicate entries for attendance summaries')
            duplicates = (
                DailyAttendanceSummary.objects.values(*unique_fields)
                    .order_by()
                    .annotate(max_id=Max('id'), count_id=Count('id'))
                    .filter(count_id__gt=1)
            )

            print('total %i duplicates attendance summaries found' % len(duplicates))
            context_dict['duplicate attendances summaries count'] = len(duplicates)

            for duplicate in duplicates:
                print(duplicate)
                (
                    DailyAttendanceSummary.objects
                        .filter(**{x: duplicate[x] for x in unique_fields})
                        .exclude(id=duplicate['max_id'])
                        .delete()
                )
            context_dict['remove_dup_attendance summaries'] = 'success'
            #
            # # 09/09/2019 - added for removing duplicate students
            # unique_fields = ['student_erp_id']
            # print('try to identify duplicate students')
            # duplicates = (
            #     Student.objects.values(*unique_fields)
            #         .order_by()
            #         .annotate(max_id=Max('id'), count_id=Count('id'))
            #         .filter(count_id__gt=1)
            # )
            #
            # print('total %i duplicates attendance summaries found' % len(duplicates))
            # context_dict['duplicate attendances summaries count'] = len(duplicates)
            #
            # for duplicate in duplicates:
            #     print(duplicate)
            #     (
            #         Student.objects
            #             .filter(**{x: duplicate[x] for x in unique_fields})
            #             .exclude(id=duplicate['max_id'])
            #             .delete()
            #     )
            # context_dict['remove duplicate students'] = 'success'

            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('exception 09072019-A from maintenance views.py %s %s' % (e.message, type(e)))
            print('failed in removing duplicate records from Attendance Table')
            context_dict['outcome'] = 'failed'
            return JSONResponse


class SMSDeliveryStatus(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        t1 = datetime.now()
        context_dict = {'start_time': '%s' % t1}
        time_threshold = datetime.now() - timedelta(hours=4.0)
        last_date = datetime(2020, 3, 20)
        print(time_threshold)
        records = SMSRecord.objects.filter(api_called=True, status_extracted=False,
                                           date__lt=time_threshold, date__gt=last_date)
        print('total %i messages delivery status to be extracted' % records.count())
        context_dict['message_count'] = records.count()

        batch = ''.join(random.choice('0123456789ABCDEF') for i in range(6))
        print('batch = %s' % batch)
        sms_batch = SMSBatch(batch=batch)
        sms_batch.total = records.count()
        success = 0
        fail = 0
        soft_sms_count = 0
        deal_sms_count = 0
        for record in records:
            print(record.date)
            recipient_number = record.recipient_number
            delivery_id = record.outcome
            print('delivery_id = %s' % delivery_id)
            print('extracting the delivery status of message with delivery id %s' % delivery_id)
            if delivery_id != '':
                if 'api' in delivery_id:
                    print('this message has been sent using SoftSMS API')
                    soft_sms_count += 1
                    try:
                        url = 'http://softsms.in/app/miscapi/'
                        key = '58fc1def26489'
                        url += key
                        url += '/getDLR/'
                        url += delivery_id
                        print('url=%s' % url)

                        response = urllib.urlopen(url)
                        status = response.read()
                        print('status = ' + str(status))
                        record.save()

                        # 19/03/2020 - a new approach to re deliver failed messages. Failed messages will be
                        # moved to another table where their delivery will be attempted by another vendor api

                        if 'Delivered' not in str(status):
                            fail += 1
                            print('this message has not been delivered will have to be re send')
                            record.status = 'Not Available'
                            record.save()
                            resend = ResendSMS(sms_record=record)
                            resend.save()
                        else:
                            success += 1

                    except Exception as e:
                        print('unable to get the staus of sms delivery. The url was: ')
                        print(url)
                        print ('Exception 10072019-A from operations maintenance views.py = %s (%s)' % (
                            e.message, type(e)))
                else:
                    print('message was sent using DealSMS API')
                    deal_sms_count += 1
                    url = 'http://148.251.80.111:5665/api/GetDeliveryStatus?api_id=API26025212584&api_password=123456789'
                    url += '&message_id=%s' % delivery_id

                    print('url = %s' % url)

                    # now extract the delivery status
                    try:
                        response = urllib.urlopen(url)
                        json_status = json.loads(response.read())
                        print(json_status)
                        del json_status['SMSMessage']
                        status = json.dumps(json_status)
                        print('delivery status = %s' % status)
                    except Exception as e:
                        print('exception 10072019-B from maintenance views.py %s %s' % (e.message, type(e)))
                        print('failed to extract he delivery status of message with id %s' % delivery_id)
                try:
                    record.status = status
                    record.status_extracted = True
                    record.save()
                    print('updated the delivery status of message with deliver_id %s' % delivery_id)
                except Exception as e:
                    print('exception 10072019-C from maintenance views.py %s %s' % (e.message, type(e)))
                    print('failed to save the extracted status of message with delivery id: %s' % delivery_id)

                # update teacher message receiver record as well
                try:
                    receiver = MessageReceivers.objects.get(status=delivery_id)
                    receiver.outcome = status
                    receiver.status_extracted = True
                    receiver.save()
                    print('updated the delivery status of Teacher Message with delivery id %s' % delivery_id)
                except Exception as e:
                    print('exception 10072019-D from maintenance views.py %s %s' % (e.message, type(e)))
                    print('failed to update Teacher Message Receiver with message id = %s' % delivery_id)
        sms_batch.success = success
        sms_batch.fail = fail
        if records.count() > 0:
            sms_batch.save()
        t2 = datetime.now()
        context_dict['end_time'] = '%s' % t2
        time_taken = t2 - t1
        context_dict['time_taken'] = time_taken
        context_dict['Soft SMS count'] = soft_sms_count
        context_dict['Deal SMS Count'] = deal_sms_count

        if records.count() > 0:
            try:
                stats = SMSDelStats(start_time=t1, end_time=t2, time_taken=float(time_taken.seconds),
                                    messages_count=records.count())
                stats.save()
                print('saved the stats for this execution')
            except Exception as e:
                print('exception 22072019 from maintenance views.py %s %s' % (e.message, type(e)))
                print('failed to store sms delivery stats into database')
        else:
            print('no message to retrieve status. Nothing stored in the db')

        return JSONResponse(context_dict, status=200)


class GetMessageCount(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        context_dict = {

        }
        yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
        date = datetime.strptime(yesterday, '%Y-%m-%d')
        print('will now retrieve the count of messages for yesterday id %s' % yesterday)

        schools = School.objects.filter()
        for school in schools:
            try:
                print('getting the count of messages sent by %s on %s...' % (school, yesterday))
                message_count = SMSRecord.objects.filter(school=school, date__gte=date,
                                                         date__lt=date + timedelta(days=1)).count()
                print('count of messages sent by %s on %s = %i' % (school, yesterday, message_count))
                sms_consumed = SMSRecord.objects.filter(school=school, date__gte=date,
                                                        date__lt=date + timedelta(days=1)).aggregate(
                    Sum('sms_consumed'))
                print(sms_consumed)
                print('count of messages sent by %s on %s = %i' % (school, yesterday, message_count))

                # store into the db
                try:
                    record = DailyMessageCount.objects.filter(school=school, date=date).first()
                    print('query for getting daily message count for %s on for date %s has been run before' %
                          (school, yesterday))
                    record.message_count = message_count

                    if sms_consumed['sms_consumed__sum'] is not None:
                        record.sms_count = sms_consumed['sms_consumed__sum']
                    else:
                        record.sms_count = 0
                    record.save()
                except Exception as e:
                    print('exception 31082019-B from maintenance views.py %s %s' % (e.message, type(e)))
                    print('query for getting daily message count for %s on for date %s has not been run before' %
                          (school, yesterday))
                    record = DailyMessageCount(school=school, date=date)
                    record.message_count = message_count
                    record.sms_count = sms_consumed['sms_consumed__sum']
                    record.save()
                print('saved the message count and sms consumption for %s on %s' % (school, yesterday))
            except Exception as e:
                print('exception 31082019-C from maintenance views.py %s %s' % (e.message, type(e)))
                print('encountered an error while extracting the message and sms count')
        context_dict['status'] = 'success'
        return JSONResponse(context_dict, status=200)
