# Send to single device.
import requests
import json

one_signal_api = '4f62be3e-1330-4fda-ac23-91757077abe3'
header = {"Content-Type": "application/json; charset=utf-8",
          "Authorization": "Basic NGEwMGZmMjItY2NkNy0xMWUzLTk5ZDUtMDAwYzI5NDBlNjJj"}

payload = {"app_id": one_signal_api,
           "include_player_ids": ["fcdf8d0d-0dfb-4b9a-b41f-8effe203792a"],
           "contents": {"en": "This push notification is through OneSignal API"}}

req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))

print(req.status_code, req.reason)

