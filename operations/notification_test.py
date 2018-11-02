import argparse
import json
import requests

from oauth2client.service_account import ServiceAccountCredentials

PROJECT_ID = 'classup-d5510'
BASE_URL = 'https://fcm.googleapis.com'
FCM_ENDPOINT = 'v1/projects/' + PROJECT_ID + '/messages:send'
FCM_URL = BASE_URL + '/' + FCM_ENDPOINT
SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']

#registration_token = 'fmeExvZ53Pk:APA91bHDPc0g01AGNKQzukUquibbuZkTA_3FU1snajpm8qJPqvt3MrZnR5r1K8raO9Mg2NOZhZycPtEr_LmaM2Y2jBxY6Tn8M3Ffg6f8nhffOHkB4zh1gYoSw1jyugj-XLzViW7lMrIR'
registration_token = 'ek3iGD_4o3M:APA91bFJug6LN4hNlDzKnYSAq8ozIiY5hGOnrbAbjn0eM3rOgaTc7HOa620xWW9e-jN_DBFzVxUdfl_K1puIAFfcAaKLJ5ub8gdRznHrxvHY_suE1C4YTZkSgSH2h2t4B3COMPAO0EbX'


# [START retrieve_access_token]
def _get_access_token():
  """Retrieve a valid access token that can be used to authorize requests.
  :return: Access token.
  """
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      'classup-d5510.json', SCOPES)
  access_token_info = credentials.get_access_token()
  return access_token_info.access_token
# [END retrieve_access_token]

def _send_fcm_message(fcm_message):
  """Send HTTP request to FCM with given message.
  Args:
    fcm_message: JSON object that will make up the body of the request.
  """
  # [START use_access_token]
  headers = {
    'Authorization': 'Bearer ' + _get_access_token(),
    'Content-Type': 'application/json; UTF-8',
  }
  # [END use_access_token]
  resp = requests.post(FCM_URL, data=json.dumps(fcm_message), headers=headers)

  if resp.status_code == 200:
    print('Message sent to Firebase for delivery, response:')
    print(resp.text)
  else:
    print('Unable to send message to Firebase')
    print(resp.text)

def _build_common_message():
  """Construct common notifiation message.
  Construct a JSON object that will be used to define the
  common parts of a notification message that will be sent
  to any app instance subscribed to the news topic.
  """
  return {
    'message': {
      'token': registration_token,
      'notification': {
        'title': 'FCM Notification',
        'body': 'Notification from FCM'
      }
    }
  }

def _build_override_message():
  """Construct common notification message with overrides.
  Constructs a JSON object that will be used to customize
  the messages that are sent to iOS and Android devices.
  """
  fcm_message = _build_common_message()

  apns_override = {
    'payload': {
      'aps': {
        'badge': 1
      }
    },
    'headers': {
      'apns-priority': '10'
    }
  }

  android_override = {
    'notification': {
      'click_action': 'android.intent.action.MAIN'
    }
  }

  fcm_message['message']['android'] = android_override
  fcm_message['message']['apns'] = apns_override

  return fcm_message

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--message')
  args = parser.parse_args()
  if args.message and args.message == 'common-message':
    common_message = _build_common_message()
    print('FCM request body for message using common notification object:')
    print(json.dumps(common_message, indent=2))
    _send_fcm_message(common_message)
  elif args.message and args.message == 'override-message':
    override_message = _build_override_message()
    print('FCM request body for override message:')
    print(json.dumps(override_message, indent=2))
    _send_fcm_message(override_message)
  else:
    print('''Invalid command. Please use one of the following commands:
python messaging.py --message=common-message
python messaging.py --message=override-message''')

if __name__ == '__main__':
  main()
