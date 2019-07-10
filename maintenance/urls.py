from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

import views

urlpatterns = [
    url(r'^de_dup/$', views.DeDup.as_view(), name='de_dup'),
    url(r'^get_delivery_status/', views.SMSDeliveryStatus.as_view(), name='get_delivery_status'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
