__author__ = 'atulmala'

from django.conf.urls import url, patterns
from operations import views

urlpatterns = patterns(
    '',
    url(r'^$', views.operations_index, name='operations_index'),

    url(r'^att_summary_school/$', views.att_summary_school, name='att_summary_school'),

    url(r'^att_summary_school_device/$', views.att_summary_school_device, name='att_summary_school_device'),

    url(r'^att_register_class/$', views.AttRegisterClass.as_view(), name='att_register_class'),

    url(r'^test_results/$', views.test_result, name='test_results'),

    url(r'^result_sms/$', views.result_sms, name='test_sms'),

    url(r'^send_message/(?P<school_id>\w+)/$', views.send_message, name='send_message'),

    url(r'^parents_communication_report/$', views.ParentCommunicationReport.as_view(),
        name='parents_communication_report'),

    url(r'^monthly_sms_report/$', views.MonthlySMSReport.as_view(), name='sms_summmary_school'),

    url(r'send_bulk_sms/$', views.send_bulk_sms, name='send_bulk_sms'),

    url(r'commit_bulk_sms/$', views.CommitBulkSMS.as_view(), name='commit_bulk_sms'),

    url(r'commit_failed_sms/$', views.CommitFailedSMS.as_view(), name='commit_failed'),

    url(r'retrieve_sms_history/(?P<parent_mobile>\w+)/$', views.SMSHistoryList.as_view()),

    url(r'send_welcome_sms/$', views.send_welcome_sms, name='send_welcome_sms'),
)
