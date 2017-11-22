from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from time_table import views

urlpatterns = [
    url(r'^setup_time_table/$', views.TheTimeTable.as_view(), name='setup_time_table'),

    url('^teacher_period/$', views.TheTeacherPeriod.as_view(), name='teacher_period'),

    url(r'^teacher_wing_mapping/$', views.TheTeacherWingMapping.as_view(), name='teacher_wing_mapping'),

    url(r'^get_arrangements/$', views.GetArrangements.as_view(), name='get_arrangements'),

    url(r'^set_arrangements/$', views.SetArrangements.as_view(), name='set_arrangements'),

    url(r'^get_arrangement_teacher/(?P<teacher>[\w.@+-]+)/$', views.ArrangementListForTeachers.as_view(),
        name='get_arrangement_teacher'),
]

urlpatterns = format_suffix_patterns(urlpatterns)