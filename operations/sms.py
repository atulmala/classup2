__author__ = 'atulgupta'

import urllib

from django.db.models import Q
from teacher.models import Teacher
from student.models import Parent
from .models import SMSRecord


def send_sms1(school, sender, mobile, message, message_type):
    print('sending to=' + mobile)

    url1 = 'http://bhashsms.com/api/sendmsg.php?user=EMERGETECH&pass=kawasaki&sender=ClssUp'
    url1 += '&phone=' + mobile
    url1 += '&text=' + message
    url1 += '&priority=ndnd&stype=normal'

    try:
        response = urllib.urlopen(url1)
        print(response.read())

        print(response)
        print (response.read().decode('utf-8'))

        # store into database
        try:
            t = Teacher.objects.get(email=sender)

            sender_name = t.first_name + ' ' + t.last_name + ' (' + sender + ')'    # include teacher's id also
            sender_type = 'Teacher'

            # because the sender is a teacher, it is obvious that the receiver is a parent
            p = Parent.objects.get(Q(parent_mobile1=mobile) | Q(parent_mobile2=mobile))
            recepient_name = p.parent_name
            recepient_type = 'Parent'

            sr = SMSRecord(school=school, sender1=sender_name, sender_type=sender_type,
                           recipient_name=recepient_name, recipient_type=recepient_type, recipient_number=mobile,
                           message=message, message_type=message_type,
                           outcome=response)
            sr.save()
        except Exception as e:

            # sender is a parent and their name was passed as sender. Hence we can use as it is
            sender_name = sender
            sender_type = 'Parent'
            t = Teacher.objects.get(mobile=mobile)
            recepient_name = t.first_name + ' ' + t.last_name
            recepient_type = 'Teacher'
            sr = SMSRecord(school=school, sender1=sender_name, sender_type=sender_type,
                           recipient_name=recepient_name, recipient_type=recepient_type, recipient_number=mobile,
                           message=message, message_type=message_type,
                           outcome=response)
            sr.save()

            print('error while trying to save sms in database')
            print ('Exception = %s (%s)' % (e.message, type(e)))

    except Exception as e:
        print ('error occured while sending sms to ' + str(mobile))
        print ('Exception = %s (%s)' % (e.message, type(e)))


def send_sms(mobile, message):
    url1 = 'http://bhashsms.com/api/sendmsg.php?user=EMERGETECH&pass=kawasaki&sender=ClssUp'
    url1 += '&phone=' + mobile
    url1 += '&text=' + message
    url1 += '&priority=ndnd&stype=normal'

    try:
        response = urllib.urlopen(url1)
        print(response.read())

        print(response)
        print (response.read().decode('utf-8'))
    except Exception as e:
        print ('error occured while sending sms to ' + str(mobile))
        print ('Exception = %s (%s)' % (e.message, type(e)))

    print('sending to=' + mobile)
    url = "http://www.smscountry.com/smscwebservice_bulk.aspx"
    values = {
        'user': 'EmergeTech',
        'passwd': 'kawasaki#1',
        'message': message,
        'mobilenumber': mobile,
        'mtype': 'N',
        'DR': 'Y'
    }

    data = urllib.urlencode(values)
    data = data.encode('utf-8')



