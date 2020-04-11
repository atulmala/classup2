# Send to single device.
import requests
import json

one_signal_api = '4f62be3e-1330-4fda-ac23-91757077abe3'
header = {
    "Content-Type": "application/json; charset=utf-8",
     "Authorization": "Basic NGEwMGZmMjItY2NkNy0xMWUzLTk5ZDUtMDAwYzI5NDBlNjJj"
}

payload = {
            "app_id": one_signal_api,
            "include_player_ids": [
                "708cb205-3554-49ea-a381-2c31b8eceea1",
                "b7f60d7b-f3af-4895-a808-2e07a7543797",
                "fcdf8d0d-0dfb-4b9a-b41f-8effe203792a",
                "2ed41f9a-7f7b-45cb-ab29-d1a91ae091de"
            ],
            "contents": {
                "en": "This push notification is through OneSignal API. https://play.google.com/store/apps/details?id=com.classup"
            },
            "url": "https://cutt.ly/GtZNFJ0"
}

req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))

outcome = '%s %s' % (req.status_code, req.reason)

print(outcome)

