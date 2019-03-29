from django.conf.urls import url, patterns

from .views import SetupAddDetails, FeeDetails, ProcessFee

urlpatterns = patterns(
    '',
    url(r'^setup_additional_details/$', SetupAddDetails.as_view(), name='setup_additional_details'),
    url(r'^fee_details/(?P<school_id>\w+)/(?P<student_id>\w+)/$', FeeDetails.as_view(), name='fee_payment',),
    url(r'^process_fee/(?P<school_id>\w+)/$', ProcessFee.as_view(), name='process_fee'),
)