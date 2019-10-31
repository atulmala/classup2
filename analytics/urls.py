__author__ = 'atulgupta'

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from analytics import views

urlpatterns = [
    url(r'^sub_analytics/(?P<school_id>\w+)/$', views.GenerateSubAnalysis.as_view(), name='sub_analytics'),
    url(r'^class_high_ave/(?P<school_id>\w+)/$', views.ClassHighestAverage.as_view(), name='class_high_ave'),
    url(r'^student_total_marks/(?P<school_id>\w+)/$',
        views.CalculateStudentTotalMarks.as_view(), name='student_total_marks'),
    url(r'performance_sheet/(?P<school_id>\w+)/(?P<the_class>\w+)/(?P<section>\w+)/(?P<selected_student>\w+)/$',
        views.StudentPerformanceAnalysis.as_view(), name='performance_sheet'),
    url(r'get_ranks/(?P<school_id>\w+)/$', views.CalculateStudentRank.as_view(), name='get_ranks'),
]

urlpatterns = format_suffix_patterns(urlpatterns)