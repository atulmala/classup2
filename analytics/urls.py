__author__ = 'atulgupta'

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from analytics import views

urlpatterns = [
    url(r'^sub_analytics/(?P<school_id>\w+)/$', views.GenerateSubAnalysis.as_view(), name='sub_analytics'),
    url(r'^class_high_ave/(?P<school_id>\w+)/$', views.ClassHighestAverage.as_view(), name='class_high_ave'),
    url(r'^student_total_marks/(?P<school_id>\w+)/$',
        views.CalculateStudentTotalMarks.as_view(), name='student_total_marks'),
]

urlpatterns = format_suffix_patterns(urlpatterns)