from pyfcm import FCMNotification

push_service = FCMNotification(api_key="AAAAntWM_N0:APA91bGgdoc-8iADBMRqiTtk4rn2KJ9VoC5AKBos26njb_b6SjDjyxpsTOOgch-7Z21--7dL9tLxo94zx6AoD7W7b9o2hSwvGy4GrSPnDQ7Xs4Ig2nKkKtXRVGKnGHAv-5uA2yKK8hQC")

# OR initialize with proxies

proxy_dict = {
    "http": "http://127.0.0.1",
    "https": "http://127.0.0.1",
}
#push_service = FCMNotification(api_key="<api-key>", proxy_dict=proxy_dict)

# Your api-key can be gotten from:  https://console.firebase.google.com/project/<project-name>/settings/cloudmessaging

registration_id = 'eK16i1uXHhI:APA91bEiEnfNrlRwYVRPPK5zPmSQwUCm_f1nK9__TRXPjXMjbn-hl-tvC9UNOxo-QjuRTIb6YVbXmHD5QS0wpEYiEjT02-Gx_oe6PYqlRse3_7FPoJLfEUbhqX1JVuS68x7xIoJkA8VM'
message_title = "welcome to classup"
message_body = "welcome to classup"
result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title,
                                           message_body=message_body)

print result

# Send to multiple devices by passing a list of ids.


print result