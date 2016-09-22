__author__ = 'atulgupta'

import urllib


def send_sms(mobile, message):
    #url1 = 'http://bhashsms.com/api/sendmsg.php?user=success&pass=654321&sender=BSHSMS' \
     #      '&phone=9871093296&text=TestSMSfromBhash&priority=ndnd&stype=normal'
    #response = urllib.urlopen(url1)
    #print(response)
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

    try:
        response = urllib.urlopen(url, data)

    except Exception as e:
        print ('error occured while sending sms to ' + str(mobile))
        print ('Exception = %s (%s)' % (e.message, type(e)))
    print (response.read().decode('utf-8'))


def send_sms_asynch(message_list):
    url = "http://www.smscountry.com/smscwebservice_bulk.aspx"

    for number in message_list:
        values = {
            'user': 'EmergeTech',
            'passwd': 'kawasaki#1',
            'message': message_list[number],
            'mobilenumber': number,
            'mtype': 'N',
            'DR': 'Y'
        }

        data = urllib.urlencode(values)
        data = data.encode('utf-8')

        try:
            response = urllib.urlopen(url, data)

        except Exception as e:
            print('error occured while sending sms to ' + str(number))
            print('Exception = %s (%s)' % (e.message, type(e)))
        print (response.read().decode('utf-8'))