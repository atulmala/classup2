import urllib2



mobile = '9871093295'
message = "Delhi is the capital of India"
sender_id = 'ClssUp'

print(message)
m1 = message.replace(" ", "+")
print(m1)
m2 = m1.replace("&", "%26")
print(m2)
url5 = 'http://softsms.in/app/smsapi/index.php?key=58fc1def26489&type=Text'
url5 +=  '&contacts=%s' % mobile
url5 += '&senderid=ClssUp&msg=%s' % m2
#print('url5 = %s' % url5)

url6 = 'http://sms.bulksmsleads.com/index.php/smsapi/httpapi/?uname=icici&password=icici&sender=icicib'
url6 += '&receiver=%s' % mobile
url6 += '&route=TA&msgtype=3'
url6 += '&sms=%s' % m2
print('url6 = %s' % url6)

try:
    print ('sending to ' + mobile)
    for n in range(0, 1):
        # now try to get the output through api
        try:
            #response3 = urllib2.urlopen(url5)
            try:
                operator = 'Bulk SMS Leads'
                while True:
                    response3 = urllib2.urlopen(url6)
                    #print('hit')
                print('response3 = ')
                r = response3.read()
                print(r)

                s1, s2 = r.split(':')
                print(s2)
                s3, s4 = s2.split('}')
                print('message id = %s' % s3)
            except Exception as e:
                print ('exception 22082018-A from sms_test.py %s %s' % (e.message, type(e)))
                print ('operator %s API is not working' % operator)
        except Exception as e:
            print('unable to send the sms. The url was: ')
            print(url5)
            print ('Exception2 from sms.py = %s (%s)' % (e.message, type(e)))
except Exception as e:
    print('unable to send sms. The url was: ')
    print(url5)
    print ('Exception3 from sms.py = %s (%s)' % (e.message, type(e)))
