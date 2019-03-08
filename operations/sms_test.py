import urllib2
import json

mobile = '9873011186'
message = 'Greetings+from+the+Chako'
api_key = '6ZWRKLTUnEmMMQro3P30SQ'
url = 'https://www.smsgatewayhub.com/api/mt/SendSMS?APIKey=%s' % api_key

senderid = 'SMSTST'
url += '&senderid=%s&channel=2&DCS=0&flashsms=0&number=%s&text=%s' % (senderid, mobile, message)


print(url)
for i in range(1):
    response = urllib2.urlopen(url)
    print('response = ')
    outcome = json.loads(response.read())
    print(outcome)
    job_id = (outcome['JobId'])
    print('job_id = ')
    print(job_id)
