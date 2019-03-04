import urllib2

mobile = '7678660426'
message = 'Greetings+from+the+Chako'
url = 'http://login.smsturtle.com/app/smsapi/index.php?key=25C7CB19C80D51&campaign=0&routeid=50&type=text'
url += '&contacts=%s' % mobile
url += '&senderid=DEMO'
url += '&msg=%s' % message
print(url)
for i in range(25):
    response = urllib2.urlopen(url)
    print('response = ')
    message_id = response.read()
    print(message_id)
    print(response.read())
AWS_ACCESS_KEY_ID = 'AKIAJ6X32EHNR26CXSWA'
AWS_SECRET_ACCESS_KEY = '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'

# Create an SNS client
# client = boto3.client(
#     "sns",
#     aws_access_key_id = AWS_ACCESS_KEY_ID,
#     aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
#     region_name = "us-east-1"
# )
#
# client.set_sms_attributes(
#     attributes={
#         'DefaultSMSType': 'Transactional',
#         'DefaultSenderID': 'CLSSUP',
#     }
# )
#
# # Send your sms message.
# result = client.publish(
#     PhoneNumber = '+917678660426',
#     Message = 'the schools will remain closed tomorrow on acccount of Diwal preparation'
# )
#
# print(result)