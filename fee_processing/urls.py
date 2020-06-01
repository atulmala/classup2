from django.conf.urls import url

from .views import FeeDetails, ProcessFee, DefaulterReport, SendMessagetoDefaulters
from .views import FeeHistory, CorrectFee, UploadFee, FeeHistoryDownload
from .views import UploadFeeDefaulters

urlpatterns = [
    url(r'^fee_details/$', FeeDetails.as_view(), name='fee_payment', ),
    url(r'^process_fee/(?P<school_id>\w+)/$', ProcessFee.as_view(), name='process_fee'),
    url(r'^defaulter_list/(?P<school_id>\w+)/$', DefaulterReport.as_view(), name='defaulter_list'),
    url(r'^get_fee_history/$', FeeHistory.as_view(), name='fee_history'),
    url(r'fee_history_download/$', FeeHistoryDownload.as_view(), name='fee_history_download'),
    url(r'^correct_fee/(?P<school_id>\w+)/$', CorrectFee.as_view(), name='correct_fee'),
    url(r'^upload_bulk_fee/$', UploadFee.as_view(), name='upload_bulk_fee'),
    url(r'^upload_fee_defaulters/(?P<school_id>\w+)/$',
        UploadFeeDefaulters.as_view(), name='upload_fee_defaulters'),
    url(r'^send_message_to_defaulters/(?P<school_id>\w+)/$',
        SendMessagetoDefaulters.as_view(), name='send_message_to_defaulters'),
]
