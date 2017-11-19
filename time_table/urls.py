from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from time_table import views

urlpatterns = [
    url(r'^setup_time_table/$', views.TheTimeTable.as_view(), name='setup_time_table'),
]

urlpatterns = format_suffix_patterns(urlpatterns)