__author__ = 'atulgupta'

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from analytics import views

urlpatterns = [
    url(r'^sub_analytics/(?P<school_id>\w+)/$', views.GenerateSubAnalysis.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)