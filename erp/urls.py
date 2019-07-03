from django.conf.urls import url, patterns

from .views import SetupAddDetails

urlpatterns = patterns(
    '',
    url(r'^setup_additional_details/$', SetupAddDetails.as_view(), name='setup_additional_details'),

)