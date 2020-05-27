from django.conf.urls import url

import views

urlpatterns = [
    url(r'^de_dup/$', views.DeDup.as_view(), name='de_dup'),
    url(r'^get_delivery_status/', views.SMSDeliveryStatus.as_view(), name='get_delivery_status'),
    url(r'^get_daily_message_count/', views.GetMessageCount.as_view(), name='get_daily_message_count'),
    url(r'^resend_failed_messages/$', views.ResendFailedMessages.as_view(), name='resend_failed_messages'),
    url(r'^delete_messages/$', views.DeleteMessages.as_view(), name='delete_messages'),
]
