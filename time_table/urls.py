from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from time_table import views

urlpatterns = [
    url(r'^setup_time_table/$', views.TheTimeTable.as_view(), name='setup_time_table'),

    url('^teacher_period/$', views.TheTeacherPeriod.as_view(), name='teacher_period'),

    url(r'^teacher_wing_mapping/$', views.TheTeacherWingMapping.as_view(), name='teacher_wing_mapping'),

    url(r'^get_arrangements/$', views.GetArrangements.as_view(), name='get_arrangements'),

    url(r'^get_arrangement_teacher/(?P<teacher>[\w.@+-]+)/$',
        views.ArrangementListForTeachers.as_view(), name='get_arrangement_teacher'),

    url(r'^set_arrangements/(?P<school_id>\w+)/$', views.SetArrangements.as_view(), name='set_arrangements'),

    url(r'^process_arrangements/$', views.AbsentTeacherPeriods.as_view(), name='process_arrangements'),

    url(r'^notify_arrangements/(?P<school_id>\w+)/$', views.NotifyArrangements.as_view(), name='notify_arrangements'),

    url(r'^download_arrangements/$', views.GetArrangements.as_view(), name='download_arrangements'),

    url(r'^generate_entry_sheet/$', views.GenerateEntrySheet.as_view(), name='generate_entry_sheet'),

    url(r'^class_time_table/$', views.ClassTimeTable.as_view(), name='class_time_table'),
]

urlpatterns = format_suffix_patterns(urlpatterns)