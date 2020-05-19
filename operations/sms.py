import requests

l__author__ = 'atulgupta'
import urllib2
import json

from django.db.models import Q
from django.contrib.auth.models import User
from authentication.models import LoginRecord, user_device_mapping
from setup.models import Configurations
from teacher.models import Teacher
from student.models import Parent
from .models import SMSRecord, SMSVendor, ParanShabd


def send_sms1(school, sender, mobile, message, message_type, *args, **kwargs):
    # 25/12/2016 - added field to check whether sms sending is enabled for this school. Check that first
    try:
        # 25/12/2016 - there will be a unique sender id for each school
        conf = Configurations.objects.get(school=school)
        sender_id = conf.sender_id
        vendor = conf.vendor_sms
        vendor_bulk_sms = conf.vendor_bulk_sms
    except Exception as e:
        print('unable to retrieve configuration')
        print ('Exception70 from sms.py = %s (%s)' % (e.message, type(e)))

    # values for softsms vendor
    print('message received in sms.py=' + message)
    m1 = message.replace(" ", "+")
    print(m1)
    m2 = m1.replace("&", "and")
    m0 = m2.replace("\n", "+")
    m00 = m0.replace("\r", "+")

    m3 = m00.replace("\r\n", "+")

    print(m3)

    # 10/04/2020 - finally after 3 years of struggle we are going to send notifications
    try:
        one_signal_api = '4f62be3e-1330-4fda-ac23-91757077abe3'
        header = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Basic NGEwMGZmMjItY2NkNy0xMWUzLTk5ZDUtMDAwYzI5NDBlNjJj"
        }
        device_mapping = user_device_mapping.objects.get(mobile_number=mobile)
        player_id = device_mapping.player_id
        unavailable = ['Not Available', 'Unavailable']
        if player_id not in unavailable:
            payload = {
                'app_id': one_signal_api,
                'include_player_ids': [player_id],
                'contents': {
                    'en': message
                }
            }
            req = requests.post("https://onesignal.com/api/v1/notifications", headers=header,
                                data=json.dumps(payload))
            print(req.status_code, req.reason)
            push_outcome = '%s %s' % (req.status_code, req.reason)
        else:
            push_outcome = 'player_id not available'
    except Exception as e:
        print('exception 10042020-A from sms.py %s %s' % (e.message, type(e)))
        push_outcome = '%s %s' % (e.message, type(e))
        print('failed to send push notification')
    print('push notification result = %s' % push_outcome)

    # first, determine the recepient & receipient type
    recepient_type = 'Undetermined'
    recepient_name = 'Undetermined'

    # in most of the cases, recepient will be parent. So, let's start with parent
    try:
        p = Parent.objects.get(Q(parent_mobile1=mobile) | Q(parent_mobile2=mobile))
        recepient_name = p.parent_name
        recepient_type = 'Parent'
        print ('recepient type is Parent')

        # 12/07/2019 - if this parent has never logged in before, include link to download the app,
        # login id and password
        # retrieve the user associated with this mobile
        try:
            print('checking whether %s has ever downloaded and logged into ClassUp before' % mobile)
            if LoginRecord.objects.filter(login_id=mobile).exists():
                print('%s has downloaded the app. No need to include download and login details' %
                      p.parent_name)
            else:
                print('%s has not downloaded the app. check whether welcome messsage to be included?' %
                      p.parent_name)
                if conf.include_welcome_sms:
                    if message_type not in ['Welcome Parent', 'Forgot Password', 'Update Student/Parent']:
                        print('welcome message to be included')

                        # check if welcome message was sent before or not
                        try:
                            upbhokta = ParanShabd.objects.get(upbhokta=mobile)
                            password = upbhokta.shabd
                            print('%s has been sent welcome message earlier. New password not generated' % mobile)
                        except Exception as e:
                            print('exception 14072019-B from sms.py %s %s' % (e.message, type(e)))
                            print('%s has not been sent a welcome message before. Password is to be generated' %
                                  mobile)
                            user = User.objects.get(username=mobile)
                            password = User.objects.make_random_password(length=5, allowed_chars='1234567890')
                            user.set_password(password)
                            user.save()
                            try:
                                p_shabd = ParanShabd(upbhokta=mobile, name=p.parent_name, shabd=password)
                                p_shabd.save()
                                print('password for %s stored. Next time will be retrieved from here only' % mobile)
                            except Exception as e:
                                print('exception 14072019-C from sms.py %s %s' % (e.message, type(e)))
                                print('failed to store password for %s' % mobile)
                        # prepare the message section and append to main message
                        m3 += '. Your user id is %s and password is %s.' % (mobile, password)
                        m3 += ' Download ClassUp and see whats happening in your child school. '
                        m3 += 'Download link Android: %s ' % conf.google_play_link
                        m3 += 'iOS: %s ' % conf.app_store_link
                        m4 = m3.replace(" ", "+")
                        m3 = m4
                        print('final message: %s' % m3)
        except Exception as e:
            print('exception 13072019-A from sms.py %s %s' % (e.message, type(e)))
            print('failed to append welcome message to %s' % mobile)
    except Exception as e:
        print ('Exception 14072019-D from sms.py = %s (%s)' % (e.message, type(e)))
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
    if message_type == 'Share Answer sheet':
        sender_type = 'Admin'
    if message_type == 'Fee Reminder':
        sender_type = 'Accounts Department'
    if message_type == 'Bulk SMS (Web Interface)' or message_type == 'Bulk SMS (Device)' \
            or message_type == 'Welcome Parent' \
            or message_type == 'Welcome Teacher' or message_type == 'Run Batch':
        sender_type = 'Admin'
        sender_name = sender
        print ('sender type is Admin')
    if message_type in [
        'Teacher Communication', 'Attendance',
        'Test Marks', 'Share Lecture'
        ]:
        # the sender must be a teacher
        sender_type = 'Teacher'
        print ('sender type is Teacher')
        try:
            t = Teacher.objects.get(email=sender)
            sender_name = t.first_name + ' ' + t.last_name + ' (' + sender + ')'  # include teacher's id also
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
        # in this case the sender can be either teacher or parent.
        # We can figure that out from recepient_type
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

    # 26/10/2018 - after getting the issues of non delivery of sms from some schools, we will now be using
    # services of at least two vendors and depending upon school category their sms will be sent through a
    # specific vendor

    # 01/07/2019 we use different vendors for bulk sms
    vendor_name = 'Undetermined !'
    vendor_retrieved = False
    if message_type == 'Bulk SMS (Device)':
        print('this is bulk sms from device. Switching to vendor specific for bulk sms')
        vendor = vendor_bulk_sms
    if vendor == 1:
        print('vendor for sending this sms for %s is softsms' % school.school_name)
        vendor_name = 'SoftSMS'
        try:
            v = SMSVendor.objects.get(vendor=vendor_name)
            vendor_retrieved = True
        except Exception as e:
            print('exception 12072019-A from sms.py %s %s' % (e.message, type(e)))
            print('could not retrieve the vendor object associated with %s' % vendor_name)

        url = 'http://softsms.in/app/smsuserapi/index.php?username=classup&userpassword=classup@123&type=text'
        url += '&contacts=%s' % mobile
        url += '&senderid=%s' % sender_id
        url += '&msg=%s' % m3

    if vendor == 3:
        print('vendor for sending this sms for %s is DealSMS' % school.school_name)
        vendor_name = 'DealSMS'
        try:
            v = SMSVendor.objects.get(vendor=vendor_name)
            vendor_retrieved = True
        except Exception as e:
            print('exception 12072019-C from sms.py %s %s' % (e.message, type(e)))
            print('could not retrieve the vendor object associated with %s' % vendor_name)
        url = 'http://148.251.80.111:5665/api/SendSMS?api_id=API26025212584&api_password=123456789'
        url += '&sms_type=T&encoding=T&sender_id=CLSSUP'
        url += '&phonenumber=%s&textmessage=%s' % (mobile, m3)
    print('url = %s' % url)
    # 06/12/2016 - we don't want to send sms to a dummy number
    if mobile == '1234567890' or len(str(mobile)) != 10:
        print ('skipping sending sms to dummy/invalid number ' + str(mobile))
    else:
        print('sending to=' + mobile)
        print('sender=' + sender)
        try:
            # 07/02/17 - we will be sending bulk sms through separate batch job as it is time consuming
            message_id = 'Not Available'
            if message_type != 'Bulk SMS (Web Interface)':
                # send the message
                if push_outcome != '200 OK':
                    print ('sending SMS to ' + mobile)
                    if conf.send_sms:
                        response = urllib2.urlopen(url)
                        if vendor == 1:
                            message_id = response.read()
                        if vendor == 2:
                            outcome = json.loads(response.read())
                            print(outcome)
                            message_id = (outcome['JobId'])
                        if vendor == 3:
                            outcome = json.loads(response.read())
                            print(outcome)
                            message_id = (outcome['message_id'])
                            # m = response.read()
                            # message_id = m[17:56]
                        print('job_id = %s' % message_id)
                        print(message_id)
                    else:
                        message_id = 'Notification'
                else:
                    message_id = 'Notification'
            else:
                print('message type was Bulk SMS (Web Interface). '
                      'Batch process to send those SMS will have to be run!')

            # 29/11/2017 - for teacher message history
            if message_type == 'Teacher Communication':
                try:
                    print ('creating Recepient records for Teacher Message History')
                    receiver = kwargs.get('receiver', None)
                    print('message_receiver = ')
                    print(receiver)
                    receiver.status = message_id
                    receiver.save()
                    print('successfully saved message receiver object')
                except Exception as e:
                    print ('exception 29112017-X from sms.py %s %s' % (e.message, type(e)))
                    print ('failed to store the status for Teacher Message History Recepient record')

            # finally, store everything into the database
            print ('going to store this sms details into the database')
            try:
                m3 = m3.replace('+', ' ')
                if vendor_retrieved:
                    sr = SMSRecord(school=school, sender1=sender_name, sender_type=sender_type,
                                   sender_code=sender_id, recipient_name=recepient_name,
                                   recipient_type=recepient_type, recipient_number=mobile, message=m3,
                                   message_type=message_type, vendor=vendor_name, the_vendor=v, outcome=message_id)
                else:
                    sr = SMSRecord(school=school, sender1=sender_name, sender_type=sender_type,
                                   sender_code=sender_id, recipient_name=recepient_name,
                                   recipient_type=recepient_type, recipient_number=mobile, message=m3,
                                   message_type=message_type, vendor=vendor_name, outcome=message_id)
                if push_outcome == '200 OK' or message_id == 'Notification':
                    sr.status_extracted = True
                    sr.status = 'Through Notification'
                sr.push_outcome = push_outcome
                # 09/04/17 when bulk sms are sent from device, they are fired instantly. The batch job need not
                # to be run if message_type == 'Bulk SMS (Web Interface)' or message_type == 'Bulk SMS (Device)':
                if message_type == 'Bulk SMS (Web Interface)':
                    # 03/05/2020 - as we have tried to send this message via notification,
                    # check if it was successfully sent. If yes, we will not send SMS
                    if push_outcome == '200 OK' or message_id == 'Notification':
                        sr.api_called = True
                    else:
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
