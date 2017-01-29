import urllib
import urllib2
import json


mobile = '9871093296'
message = 'testing for delivery confirmation see whether & character is delivered or not'
sender_id = 'MDLSCL'
authkey = '138436Aff1HY1Vurw588743cf'
rout = 'default'
values = {
    'authkey': authkey,
    'mobiles': mobile,
    'message': message,
    'sender': sender_id,
    'rout': rout,
    'response': 'json',
    'flash': 1
}
url3 = 'https://control.msg91.com/api/sendhttp.php'
print(url3)


try:
    print ('sending to ' + mobile)
    postdata = urllib.urlencode(values)
    req = urllib2.Request(url3, postdata)
    # job_id = '33922227'
    response = urllib2.urlopen(req)
    #print(response.read())
    j = json.loads(response.read())
    message_id = j['message']
    print(message_id)

    # now try to get the output through api
    try:
        url4 = 'https://control.msg91.com/api/getDlrReport.php?authkey='
        url4 += authkey
        url4 += '&reqId='
        url4 += message_id
        print(url4)
        response2 = urllib2.urlopen(url4)
        j1 = json.loads(response2.read())
        print j1
    except Exception as e:
        print('unable to get the staus of sms delivery through api. The url was: ')
        print(url4)
        print ('Exception1 from sms.py = %s (%s)' % (e.message, type(e)))

    # get delivery report through webhooks
    try:
        url5 = 'https://www.classupclient.com/operations/webhooks'
        #response3 = urllib2.urlopen(url5)
        #print(response3.read())
    except Exception as e:
        print('unable to get the status using webhook. The url was: ')
        print(url5)
        print ('Exception2 from sms.py = %s (%s)' % (e.message, type(e)))
except Exception as e:
    print('unable to send sms. The url was: ')
    print(url3)
    print ('Exception3 from sms.py = %s (%s)' % (e.message, type(e)))
