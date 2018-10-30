import requests
import boto3


# url = "http://sms.bulksmsleads.com/index.php/Bulksmsapi/httpapi/"
#
# querystring = {"uname":"classup","password":"classup","sender":"CLSSUP","receiver":"7678660426",
#                "route":"TA","msgtype":"1",
#                "sms":"Dear+Amit+Chauhan,+message+regarding+Aanav:+please+send+janmashtmi+material+from+emulator.+Regards,+ClassUp+RTS,+Radisson+The+School"}
#
# payload = "------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"uname\"\r\n\r\nclassup\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"password\"\r\n\r\nclassup\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"sender\"\r\n\r\nclssup\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"receiver\"\r\n\r\n7678660426\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"route\"\r\n\r\nTA\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"msgtype\"\r\n\r\n1\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"sms\"\r\n\r\nPlease send art material for janmashtmi celebration\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--"
# headers = {
#     'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
#     'Cache-Control': "no-cache",
#     'Postman-Token': "70c0fb28-1b16-8514-b05d-22d377d0151c"
#     }
#
# response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
AWS_ACCESS_KEY_ID = 'AKIAJ6X32EHNR26CXSWA'
AWS_SECRET_ACCESS_KEY = '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'

# Create an SNS client
client = boto3.client(
    "sns",
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name = "us-east-1"
)

client.set_sms_attributes(
    attributes={
        'DefaultSMSType': 'Transactional',
        'DefaultSenderID': 'CLSSUP',
    }
)

# Send your sms message.
result = client.publish(
    PhoneNumber = '+917678660426',
    Message = 'the schools will remain closed tomorrow on acccount of Diwal preparation'
)

print(result)