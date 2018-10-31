# custom_storages.py
from django.conf import settings
from storages.backends.s3boto import S3BotoStorage
from storages.backends.gcloud import GoogleCloudStorage


class StaticStorage(GoogleCloudStorage):
    location = settings.STATICFILES_LOCATION

class MediaStorage(GoogleCloudStorage):
    location = settings.MEDIAFILES_LOCATION