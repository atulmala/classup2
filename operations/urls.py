__author__ = 'atulmala'

from django.conf.urls import url, patterns
from operations import views

urlpatterns = patterns(
    '',
    url(r'^$', views.operations_index, name='operations_index'),
    url(r'^att_summary_school/$', views.att_summary_school, name='att_summary_school'),
    url(r'^att_register_class/$', views.att_register_class, name='att_register_class'),
    url(r'^test_results/$', views.test_result, name='test_results'),
    url(r'^result_sms/$', views.result_sms, name='test_sms'),
    url(r'^send_message/(?P<school_id>\w+)/$', views.send_message, name='send_message'),
    url(r'^parents_communication_details/$', views.parents_communication_details, name='parents_communication_details'),
    url(r'^sms_summary_school/$', views.sms_summary, name='sms_summmary_school'),
    url(r'send_bulk_sms/$', views.send_bulk_sms, name='send_bulk_sms'),
    url(r'retrieve_sms_history/(?P<parent_mobile>\w+)/$', views.SMSHistoryList.as_view()),
)
