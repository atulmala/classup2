__author__ = 'atulgupta'

import urllib

from django.db.models import Q
from teacher.models import Teacher
from student.models import Parent
from .models import SMSRecord


def send_sms1(school, sender, mobile, message, message_type):
    print('sending to=' + mobile)
    print('sender=' + sender)

    url1 = 'http://bhashsms.com/api/sendmsg.php?user=EMERGETECH&pass=kawasaki&sender=ClssUp'
    url1 += '&phone=' + mobile
    url1 += '&text=' + message
    url1 += '&priority=ndnd&stype=normal'

    try:
        response = urllib.urlopen(url1)

        try:
            message_id = response.read()
            url2 = 'http://bhashsms.com/api/recdlr.php?user=EMERGETECH&msgid='
            url2 += message_id
            url2 += '&phone='
            url2 += mobile
            url2 += '&msgtype='
            url2 += message_id
            outcome = urllib.urlopen(url2)
            status = outcome.read()
            status += ' (url = ' + url2 + ')'
            print(status)
        except Exception as e:
            print('unable to get the staus of sms delivery. The url was: ')
            print(url2)
            print ('Exception10 from sms.py = %s (%s)' % (e.message, type(e)))

        # store into database
        try:
            t = Teacher.objects.get(email=sender)
            sender_name = t.first_name + ' ' + t.last_name + ' (' + sender + ')'    # include teacher's id also

            sender_type = 'Teacher'
            if message_type == 'Bulk SMS (Web Interface)' or message_type == 'Welcome Parent' \
                    or message_type == 'Welcome Teacher':
                sender_type = 'Admin'

            try:
                # because the sender is a teacher, it is obvious that the receiver is a parent
                p = Parent.objects.get(Q(parent_mobile1=mobile) | Q(parent_mobile2=mobile))
                recepient_name = p.parent_name
                recepient_type = 'Parent'
            except Exception as e:
                # from web interface bulk sms are also sent to teachers. In this case recipient is a teacher
                print('unable to associate parent with ' + mobile + ' May this belongs to teacher...')
                print ('Exception4 from sms.py = %s (%s)' % (e.message, type(e)))
                t = Teacher.objects.get(mobile=mobile)
                recepient_name = t.first_name + ' ' + t.last_name
                recepient_type = 'Teacher'

            try:
                sr = SMSRecord(school=school, sender1=sender_name, sender_type=sender_type,
                               recipient_name=recepient_name, recipient_type=recepient_type, recipient_number=mobile,
                               message=message, message_type=message_type,
                               outcome=status)
                sr.save()
            except Exception as e:
                print ('error occured while sending sms to ' + str(mobile))
                print ('Exception3 from sms.py = %s (%s)' % (e.message, type(e)))
        except Exception as e:

            # sender is a parent and their name was passed as sender. Hence we can use as it is
            sender_name = sender
            sender_type = 'Parent'

            try:
                t = Teacher.objects.get(mobile=mobile)
                recepient_name = t.first_name + ' ' + t.last_name
                recepient_type = 'Teacher'
                sr = SMSRecord(school=school, sender1=sender_name, sender_type=sender_type,
                               recipient_name=recepient_name, recipient_type=recepient_type, recipient_number=mobile,
                               message=message, message_type=message_type,
                               outcome=status)
                sr.save()
            except Exception as e:
                # this will happen when a parent tries to reset password. Both sender and receiver is parent,
                # hence the above query will fail
                print('looks like a case of password reset by parent...')
                print ('Exception5 from sms.py = %s (%s)' % (e.message, type(e)))
                sender_type = 'Parent'
                recepient_type = 'Parent'
                try:
                    p = Parent.objects.get(Q(parent_mobile1=mobile) | Q(parent_mobile2=mobile))
                    sender_name = p.parent_name
                    recepient_name = p.parent_name
                    sr = SMSRecord(school=school, sender1=sender_name, sender_type=sender_type,
                                   recipient_name=recepient_name, recipient_type=recepient_type,
                                   recipient_number=mobile, message=message, message_type=message_type,
                                   outcome=status)
                    sr.save()
                except Exception as e:
                    print ('error occured while trying to save sms for:  ' + str(mobile))
                    print ('Exception6 from sms.py = %s (%s)' % (e.message, type(e)))

    except Exception as e:
        print ('error occured while sending sms to ' + str(mobile) + '. The url was: ')
        print(url1)
        print ('Exception2 from sms.py = %s (%s)' % (e.message, type(e)))


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



