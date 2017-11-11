__author__ = 'atulgupta'

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from teacher import views

urlpatterns = [
    url(r'^teacher_subject_list/(?P<teacher>[\w.@+-]+)/$', views.TeacherSubjectList .as_view()),

    url(r'^set_subjects/(?P<teacher>[\w.@+-]+)/$', views.set_subjects, name='set_subjects'),

    url(r'^unset_subjects/(?P<teacher>[\w.@+-]+)/$', views.unset_subjects, name='unset_subjects'),

    url(r'^add_teacher/$', views.add_teacher, name='add_teacher'),

    url(r'^teacher_list/(?P<school_id>\w+)/$', views.TeacherList.as_view()),

    url(r'^whether_class_teacher/(?P<teacher_id>\w+)/$', views.whether_class_teacher, name='whether_class_teacher'),

    url(r'^whether_class_teacher2/(?P<teacher>[\w.@+-]+)/$', views.whether_class_teacher2),

    url(r'^delete_teacher/$', views.delete_teacher, name='delete_teacher'),

    url(r'^update_teacher/$', views.update_teacher, name='update_teacher'),

    url(r'^retrieve_attendance/(?P<school_id>\w+)/(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/$',
        views.TheTeacherAttendance.as_view(), name='retrieve_attendance'),

    url(r'^process_attendance/(?P<school_id>\w+)/(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/$',
        views.TheTeacherAttendance.as_view(), name='process_attendance'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
