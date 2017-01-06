import urllib
import json
import time

mobile = '9871093296'
message = 'testing for delivery confirmation'
sender_id = 'MDLSCL'
url3 = 'http://smppsmshub.in/api/mt/SendSMS?user=atulg&password=atulg'
url3 += '&senderid=' + sender_id
url3 += '&channel=Trans&DCS=0&flashsms=0'
url3 += '&number=' + mobile
url3 += '&text=' + message
url3 += '&route=28'
print(url3)

try:
    print ('sending to ' + mobile)

    # job_id = '33922227'
    response = urllib.urlopen(url3)
    j = json.loads(response.read())
    job_id = j['JobId']
    trailer = '&jobid='
    trailer += job_id
    print('job_id=' + job_id)

    try:
        url4 = 'http://smppsmshub.in/api/mt/GetDelivery'
        url4 += '?user=atulg&password=atulg'
        url4 += trailer
        # url4.strip()
        print('going to sleep...')
        time.sleep(5)
        print('wake up from sleep')
        try:
            response2 = urllib.urlopen(url4)
            j2 = json.loads(response2.read())
            print j2
            status = j2['DeliveryReports'][0]['DeliveryStatus'] + ' at '
            status += j2['DeliveryReports'][0]['DeliveryDate']
            print('status(smppsmshub)=' + str(status))
        except Exception as e:
            print('unable to get the staus of sms delivery. The url was: ')
            print(url4)
            print ('Exception10 from sms.py = %s (%s)' % (e.message, type(e)))
    except Exception as e:
        print('unable to get the staus of sms delivery. The url was: ')
        print(url3)
        print ('Exception10 from sms.py = %s (%s)' % (e.message, type(e)))
except Exception as e:
    print('unable to get the staus of sms delivery. The url was: ')
    print(url3)
    print ('Exception10 from sms.py = %s (%s)' % (e.message, type(e)))
