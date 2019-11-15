from __future__ import print_function
import clicksend_client
from clicksend_client import SmsMessage
from clicksend_client.rest import ApiException


# Configure HTTP basic authorization: BasicAuth
configuration = clicksend_client.Configuration()
configuration.username = 'atul.gupta@classup.in'
configuration.password = 'FFB1E530-5CB9-CD36-0135-5F0C5D206FBB'

# create an instance of the API class
api_instance = clicksend_client.SMSApi(clicksend_client.ApiClient(configuration))
sms_message = SmsMessage(source="php",
                        body="hi Vibhuti this is a message from ClassUp.",
                        to="+18049388789",
                        schedule=1436874701)
sms_messages = clicksend_client.SmsMessageCollection(messages=[sms_message])

try:
    # Send sms message(s)
    api_response = api_instance.sms_send_post(sms_messages)
    print(api_response)
except ApiException as e:
    print("Exception when calling SMSApi->sms_send_post: %s\n" % e)