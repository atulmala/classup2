import urllib


from django.db.models import Count, Max
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework import generics

from datetime import datetime, timedelta

from attendance.models import Attendance, DailyAttendanceSummary
from operations.models import SMSRecord
from teacher.models import MessageReceivers

from .models import SMSDelStats


class JSONResponse(HttpResponse):
    """
    an HttpResponse that renders its contents to JSON
    """

    def __init__(self, data, **kwargs):
        print ('from JSONResponse...')
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class DeDup(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        context_dict = {

        }

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

            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('exception 09072019-A from maintenance views.py %s %s' % (e.message, type(e)))
            print('failed in removing duplicate records from Attendance Table')
            context_dict['outcome'] = 'failed'
            return JSONResponse


class SMSDeliveryStatus(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        t1 = datetime.now()
        context_dict = {

        }
        context_dict['start_time'] = '%s' % t1
        time_threshold = datetime.now() - timedelta(hours=2.5)
        last_date = datetime(2019, 7, 8)
        print(time_threshold)
        records = SMSRecord.objects.filter(api_called=True, status_extracted=False,
                                           date__lt=time_threshold, date__gt=last_date)
        print('total %i messages delivery status to be extracted' % records.count())
        context_dict['message_count'] = records.count()

        soft_sms_count = 0
        deal_sms_count = 0
        for record in records:
            print(record.date)
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
                    except Exception as e:
                        print('unable to get the staus of sms delivery. The url was: ')
                        print(url)
                        print ('Exception 10072019-A from operations maintenance views.py = %s (%s)' % (e.message, type(e)))
                else:
                    print('message was sent using DealSMS API')
                    deal_sms_count += 1
                    url = 'http://5.9.69.238/reports/getByMid.php?uname=classup&password=56tr43we'
                    the_date = record.date.strftime('%Y-%m-%d')
                    url += '&sdate=%s' % the_date
                    url += '&mid=%s' % delivery_id
                    print('url = %s' % url)

                    # now extract the delivery status
                    try:
                        response = urllib.urlopen(url)
                        status = response.read()
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
