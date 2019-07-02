from django.conf.urls import url, patterns

from .views import SetupAddDetails, FeeDetails, ProcessFee, DefaulterReport, FeeHistory, CorrectFee, UploadFee

urlpatterns = patterns(
    '',
    url(r'^setup_additional_details/$', SetupAddDetails.as_view(), name='setup_additional_details'),
    url(r'^fee_details/$', FeeDetails.as_view(), name='fee_payment',),
    url(r'^process_fee/(?P<school_id>\w+)/$', ProcessFee.as_view(), name='process_fee'),
    url(r'^defaulter_list/(?P<school_id>\w+)/$', DefaulterReport.as_view(), name='defaulter_list'),
    url(r'^get_fee_history/$', FeeHistory.as_view(), name='fee_history'),
    url(r'^correct_fee/(?P<school_id>\w+)/$', CorrectFee.as_view(), name='correct_fee'),
    url(r'^upload_bulk_fee/$', UploadFee.as_view(), name='upload_bulk_fee'),
)