__author__ = 'atulgupta'

import urllib


def send_sms(mobile, message):
    url1 = 'http://bhashsms.com/api/sendmsg.php?user=EMERGETECH&pass=kawasaki&sender=ClssUp'
    url1 += '&phone=' + mobile
    url1 += '&text=' + message
    url1 += '&priority=ndnd&stype=normal'
    #print(url1)
    # try:
    #     response = urllib.urlopen(url1)
    #     print(response)
    #     print (response.read().decode('utf-8'))
    # except Exception as e:
    #     print ('error occured while sending sms to ' + str(mobile))
    #     print ('Exception = %s (%s)' % (e.message, type(e)))




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

    try:
        response = urllib.urlopen(url, data)

    except Exception as e:
        print('error occured while sending sms to ' + str(mobile))
        print('Exception = %s (%s)' % (e.message, type(e)))
        print (response.read().decode('utf-8'))




def send_sms_asynch(message_list):
    url = "http://www.smscountry.com/smscwebservice_bulk.aspx"

    url1 = 'http://bhashsms.com/api/sendmsg.php?user=EMERGETECH&pass=kawasaki&sender=ClssUp'



    for number in message_list:

        url1 += '&phone=' + str(number)
        url1 += '&text=' + message_list[number]
        url1 += '&priority=ndnd&stype=normal'
        print(url1)
        try:
            response = urllib.urlopen(url1)
            print(response)
            print (response.read().decode('utf-8'))
        except Exception as e:
            print ('error occured while sending sms to ' + str(number))
            print ('Exception = %s (%s)' % (e.message, type(e)))

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