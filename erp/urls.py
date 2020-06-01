from django.conf.urls import url

from .views import SetupAddDetails

urlpatterns = [
    url(r'^setup_additional_details/$', SetupAddDetails.as_view(),
        name='setup_additional_details'),
]
