from django.conf.urls import url, patterns

from .views import SetupAddDetails, FeePayment

urlpatterns = patterns(
    '',
    url(r'^setup_additional_details/$', SetupAddDetails.as_view(), name='setup_additional_details'),
    url(r'^fee_payment/(?P<school_id>\w+)/(?P<student_id>\w+)/$', FeePayment.as_view(), name='fee_payment',)
)