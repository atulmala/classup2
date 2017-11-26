l__author__ = 'atulgupta'

import urllib
import urllib2
import json

from django.db.models import Q
from authentication.models import user_device_mapping
from push_notifications.models import GCMDevice
from setup.models import Configurations
from teacher.models import Teacher
from student.models import Parent
from .models import SMSRecord

from push_notifications.gcm import gcm_send_message


def send_sms1(school, sender, mobile, message, message_type):
    # 25/12/2016 - added field to check whether sms sending is enabled for this school. Check that first
    try:
        # 25/12/2016 - there will be a unique sender id for each school
        conf = Configurations.objects.get(school=school)
        sender_id = conf.sender_id
    except Exception as e:
        print('unable to retrieve configuration')
        print ('Exception70 from sms.py = %s (%s)' % (e.message, type(e)))

    if conf.send_sms:
        # values for softsms vendor
        key = '58fc1def26489'

        m1 = message.replace(" ", "+")
        print(m1)
        m2 = m1.replace("&", "%26")
        m0 = m2.replace("\n", "+")
        m00 = m0.replace("\r", "+")

        m3 = m00.replace("\r\n", "+")

        print(m3)

        url = 'http://softsms.in/app/smsapi/index.php?'
        url+= 'key=%s' % key
        url += '&type=Text'
        url += '&contacts=%s' % mobile
        url += '&senderid=%s' % sender_id
        url += '&msg=%s' % m3
        print('url=%s' % url)

        # 06/12/2016 - we don't want to send sms to a dummy number
        if mobile == '1234567890' or len(str(mobile)) != 10:
            print ('skipping sending sms to dummy/invalid number ' + str(mobile))
        else:
            print('sending to=' + mobile)
            print('sender=' + sender)
            print('message received in sms.py=' + message)

            try:
                # 07/02/17 - we will be sending bulk sms through separate batch job as it is time consuming
                message_id = 'Not Available'
                if message_type != 'Bulk SMS (Web Interface)':
                    # send the message
                    print ('sending to ' + mobile)

                    response = urllib2.urlopen(url)
                    print('response = ')
                    message_id = response.read()
                    print(message_id)

                    # 23/03/17 send notification also if we have the device token of this mobile number
                    try:
                        device_token = user_device_mapping.objects.get(mobile_number=mobile)
                        print('device token exist for ' + str(mobile))
                        print('now trying to send push notification to ' + str(mobile))
                        try:
                            fcm_device = GCMDevice.objects.get(registration_id=device_token)
                            fcm_device.send_message(message)
                        except Exception as e:
                            print('Exception 170 from sms.py  %s (%s)' % (e.message, type(e)))
                            print('failed to push notification via fcm_device.send() to ' + str(mobile))
                        gcm_send_message(device_token, {'body': message})
                    except Exception as e:
                        print('Exception 160 from sms.py  %s (%s)' % (e.message, type(e)))
                        print('failed to push notification to ' + str(mobile))

                else:
                    print('message type was Bulk SMS (Web Interface). '
                          'Batch process to send those SMS will have to be run!')

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
                print('message type = %s' % message_type)
                if message_type == 'Bulk SMS (Web Interface)' or message_type == 'Bulk SMS (Device)'\
                        or message_type == 'Welcome Parent' \
                        or message_type == 'Welcome Teacher' or message_type == 'Run Batch':
                    sender_type = 'Admin'
                    sender_name = sender
                    print ('sender type is Admin')

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
                    sr = SMSRecord(school=school, sender1=sender_name, sender_type=sender_type, sender_code=sender_id,
                                    recipient_name=recepient_name, recipient_type=recepient_type,
                                   recipient_number=mobile, message=message, message_type=message_type,
                                    outcome=message_id)
                    # 09/04/17 when bulk sms are sent from device, they are fired instantly. The batch job need not to be run
                    #if message_type == 'Bulk SMS (Web Interface)' or message_type == 'Bulk SMS (Device)':
                    if message_type == 'Bulk SMS (Web Interface)':
                        print('api called status has been set to false. Can be turned true only by running batch job')
                        sr.api_called = False
                    else:
                        print('api called status has been set to true. ')
                        sr.api_called = True
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
