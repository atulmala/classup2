__author__ = 'atulgupta'

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from teacher import views

urlpatterns = [
    url(r'^teacher_subject_list/(?P<teacher>[\w.@+-]+)/$', views.TeacherSubjectList .as_view()),
    url(r'^set_subjects/(?P<teacher>[\w.@+-]+)/$', views.set_subjects, name='set_subjects'),
    url(r'^unset_subjects/(?P<teacher>[\w.@+-]+)/$', views.unset_subjects, name='unset_subjects'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
