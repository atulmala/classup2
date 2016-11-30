__author__ = 'atulgupta'

import urllib

from django.db.models import Q
from teacher.models import Teacher
from student.models import Parent
from .models import SMSRecord


def send_sms2(school, sender, mobile, message, message_type):
    print('sending to=' + mobile)
    print('sender=' + sender)
    print('message received in sms.py=' + message)

    url1 = 'http://bhashsms.com/api/sendmsg.php?user=EMERGETECH&pass=kawasaki&sender=ClssUp'
    url1 += '&phone=' + mobile
    url1 += '&text=' + message
    url1 += '&priority=ndnd&stype=normal'

    try:
        response = urllib.urlopen(url1)

        # now get the outcome of the message sending call above
        message_id = response.read()

        # 29/11/2016 - in case of bulk messaging (bulk sms, welcome parent/teacher at the time of setup,
        # retrieving outcome can be time consuming and result into 504 - Gateway timeout. Hence let us just
        # store the message id which can be used to retrieve the status from Bhash SMS portal
        if message_type == 'Bulk SMS (Web Interface)' or message_type == 'Welcome Parent' \
                or message_type == 'Welcome Teacher':
            status = 'Please use this message id to retrieve from SMS provider portal: ' + message_id
        else:
            try:

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
        sender_type = 'Unknown'
        if message_type == 'Bulk SMS (Web Interface)' or message_type == 'Welcome Parent' \
                or message_type == 'Welcome Teacher':
            sender_type = 'Admin'

        try:
            t = Teacher.objects.get(email=sender)
            sender_name = t.first_name + ' ' + t.last_name + ' (' + sender + ')'    # include teacher's id also

            sender_type = 'Teacher'


            try:
                # because the sender is a teacher, it is obvious that the receiver is a parent
                p = Parent.objects.get(Q(parent_mobile1=mobile) | Q(parent_mobile2=mobile))
                recepient_name = p.parent_name
                recepient_type = 'Parent'
            except Exception as e:
                # from web interface bulk sms are also sent to teachers. In this case recipient is a teacher
                # also, when a teacher tries to reset his/her password then also recipient is teacher
                print('unable to associate parent with ' + mobile + ' May this belongs to teacher...')
                print ('Exception4 from sms.py = %s (%s)' % (e.message, type(e)))
                t = Teacher.objects.get(school=school, mobile=mobile)
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
                t = Teacher.objects.get(school=school, mobile=mobile)
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

def send_sms1(school, sender, mobile, message, message_type):
    print('sending to=' + mobile)
    print('sender=' + sender)
    print('message received in sms.py=' + message)

    url1 = 'http://bhashsms.com/api/sendmsg.php?user=EMERGETECH&pass=kawasaki&sender=ClssUp'
    url1 += '&phone=' + mobile
    url1 += '&text=' + message
    url1 += '&priority=ndnd&stype=normal'

    try:
        # send the message
        response = urllib.urlopen(url1)

        # now get the outcome of the message sending call above
        message_id = response.read()

        # 29/11/2016 - in case of bulk messaging (bulk sms, welcome parent/teacher at the time of setup,
        # retrieving outcome can be time consuming and result into 504 - Gateway timeout. Hence let us just
        # store the message id which can be used to retrieve the status from Bhash SMS portal
        if message_type == 'Bulk SMS (Web Interface)' or message_type == 'Welcome Parent' \
                or message_type == 'Welcome Teacher':
            status = 'Please use this message id to retrieve from SMS provider portal: ' + message_id
        else:
            try:
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

        if message_type == 'Teacher Communication' or message_type == 'Attendance':
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
                    #t = Teacher.objects.get(email=sender)
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
                            outcome=status)
            sr.save()
        except Exception as e:
            print ('Exception54 from sms.py = %s (%s)' % (e.message, type(e)))
            print ('error occured while trying to save sms record for  ' + str(mobile))

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



