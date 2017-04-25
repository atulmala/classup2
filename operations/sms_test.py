import urllib
import urllib2
import json


mobile = '7678660426'
message = "your ward was absent & you need to send an application"
sender_id = 'ClssUp'

print(message)
m1 = message.replace(" ", "+")
print(m1)
m2 = m1.replace("&", "%26")
print(m2)
url5 = 'http://softsms.in/app/smsapi/index.php?key=58fc1def26489&type=Text'
url5 +=  '&contacts=%s' % mobile
url5 += '&senderid=ClssUp&msg=%s' % m2

print('url5 = %s' % url5)

try:
    print ('sending to ' + mobile)
    for n in range(0, 25):
        # now try to get the output through api
        try:
            response3 = urllib2.urlopen(url5)
            print('response3 = ')
            print(response3.read())
        except Exception as e:
            print('unable to send the sms. The url was: ')
            print(url5)
            print ('Exception2 from sms.py = %s (%s)' % (e.message, type(e)))
except Exception as e:
    print('unable to send sms. The url was: ')
    print(url5)
    print ('Exception3 from sms.py = %s (%s)' % (e.message, type(e)))
