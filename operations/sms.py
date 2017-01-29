__author__ = 'atulgupta'

import urllib
import urllib2
import json

from django.db.models import Q
from setup.models import School, Configurations
from teacher.models import Teacher
from student.models import Parent
from .models import SMSRecord

def send_sms1(school, sender, mobile, message, message_type):
    # 25/12/2016 - added field to check whether sms sending is enabled for this school. Check that first
    try:
        conf = Configurations.objects.get(school=school)
        # 25/12/2016 - there will be a unique sender id for each school
        sender_id = conf.sender_id
    except Exception as e:
        print('unable to retrieve configuration')
        print ('Exception70 from sms.py = %s (%s)' % (e.message, type(e)))

    if conf.send_sms:
        # 29/01/17 - values for msg91 vendor
        authkey = '138436Aff1HY1Vurw588743cf'
        rout = 'default'
        values = {
            'authkey': authkey,
            'mobiles': mobile,
            'message': message,
            'sender': sender_id,
            'rout': rout,
            'response': 'json',
        }
        url3 = 'https://control.msg91.com/api/sendhttp.php'
        print(url3)
        postdata = urllib.urlencode(values)

        # 06/12/2016 - we don't want to send sms to a dummy number
        if mobile == '1234567890' or len(str(mobile)) != 10:
            print ('skipping sending sms to dummy/invalid number ' + str(mobile))
        else:
            print('sending to=' + mobile)
            print('sender=' + sender)
            print('message received in sms.py=' + message)
            url = 'http://smppsmshub.in/api/mt/SendSMS?user=atulg&password=atulg'
            url += '&senderid=' + sender_id
            url += '&channel=Trans&DCS=0&flashsms=0'
            url += '&number=' + mobile
            url += '&text=' + message
            url += '&route=28'

            try:
                # send the message
                print ('sending to ' + mobile)

                # req = urllib2.Request(url3, postdata)
                # response = urllib2.urlopen(req)
                # j = json.loads(response.read())
                # message_id = j['message']
                # print(message_id)

                response = urllib.urlopen(url)
                j = json.loads(response.read())
                message_id = str(j['JobId'])
                print('status (job_id) = ' + message_id)

                # first, determine the recepient & receipient type
                recepient_type = 'Undetermined'
                recepient_name = 'Undetermined'

                # in most of the cases, recepient will be parent. So, let's start with parent
                try:
                    p = Parent.objects.get(Q(parent_mobile1=mobile) | Q(parent_mobile2=mobile))
                    recepient_name = p.parent_name
                    recepient_type = 'Parent'
                    print ('recepient type is Parent')
                except Exception as e:
                    print ('Exception50 from sms.py = %s (%s)' % (e.message, type(e)))
                    print('The recepient is not a parent. This must be a teacher')

                    try:
                        t = Teacher.objects.get(school=school, mobile=mobile)
                        recepient_name = t.first_name + ' ' + t.last_name
                        recepient_type = 'Teacher'
                        print ('recepient type is Teacher')
                    except Exception as e:
                        print ('Exception51 from sms.py = %s (%s)' % (e.message, type(e)))
                        print('The recepient type & name Undetermined')

                # next, determine the sender details
                sender_type = 'Undetermined'
                sender_name = sender
                if message_type == 'Bulk SMS (Web Interface)' or message_type == 'Welcome Parent' \
                        or message_type == 'Welcome Teacher':
                    sender_type = 'Admin (Web Interface)'
                    sender_name = sender
                    print ('sender type is Admin (Web Interface)')

                if message_type == 'Teacher Communication' or message_type == 'Attendance' or \
                                message_type == 'Test Marks':
                    # the sender must be a teacher
                    sender_type = 'Teacher'
                    print ('sender type is Teacher')
                    try:
                        t = Teacher.objects.get(email=sender)
                        sender_name = t.first_name + ' ' + t.last_name + ' (' + sender + ')'    # include teacher's id also
                    except Exception as e:
                        print ('Exception60 from sms.py = %s (%s)' % (e.message, type(e)))
                        print('the message type is Teacher Communication/Attendance, '
                              'but the teacher name Undetermined')

                if message_type == 'Parent Communication':
                    # the sender must be a parent
                    sender_type = 'Parent'
                    print ('sender type is Parent')
                    try:
                        p = Parent.objects.get(Q(parent_mobile1=mobile) | Q(parent_mobile2=mobile))
                        sender_name = p.parent_name
                    except Exception as e:
                        print ('Exception52 from sms.py = %s (%s)' % (e.message, type(e)))
                        print('the message type is Parent Communication, '
                              'but the parent name Undetermined')

                if message_type == 'Forgot Password':
                    # in this case the sender can be either teacher or parent. We can figure that out from recepient_type
                    if recepient_type == 'Parent':
                        print ('sender type is Parent')
                        # the sender will also be a parent (actually sender and receiver would be the same)
                        try:
                            p = Parent.objects.get(Q(parent_mobile1=mobile) | Q(parent_mobile2=mobile))
                            sender_name = p.parent_name
                            sender_type = 'Parent'

                        except Exception as e:
                            print ('Exception53 from sms.py = %s (%s)' % (e.message, type(e)))
                            print('the message type Password Reset for parent, '
                                  'but the parent name Undetermined')

                    if recepient_type == 'Teacher':
                        print ('sender type is Teacher')
                        # the sender will also be a teacher (actually sender and receiver would be the same)
                        try:
                            t = Teacher.objects.get(school=school, mobile=mobile)
                            sender_name = t.first_name + ' ' + t.last_name + ' (' + sender + ')'  # include teacher's id also
                        except Exception as e:
                            print ('Exception51 from sms.py = %s (%s)' % (e.message, type(e)))
                            print('the message type Password Reset for teacher, '
                                  'but the teacher name Undetermined')

                # finally, store everything into the database
                print ('going to store this sms details into the database')
                try:
                    sr = SMSRecord(school=school, sender1=sender_name, sender_type=sender_type,
                                    recipient_name=recepient_name, recipient_type=recepient_type, recipient_number=mobile,
                                    message=message, message_type=message_type,
                                    outcome=message_id)
                    sr.save()
                except Exception as e:
                    print ('Exception54 from sms.py = %s (%s)' % (e.message, type(e)))
                    print ('error occured while trying to save sms record for  ' + str(mobile))

            except Exception as e:
                print ('error occured while sending sms to ' + str(mobile) + '. The url was: ')
                print(url)
                print ('Exception2 from sms.py = %s (%s)' % (e.message, type(e)))
    else:
        print ('Send SMS is turned off for this school: ' + school.school_name + ', ' + school.school_address)
