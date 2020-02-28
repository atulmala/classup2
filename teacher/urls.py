__author__ = 'atulgupta'

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from teacher import views

urlpatterns = [
    url(r'^teacher_subject_list/(?P<teacher>[\w.@+-]+)/$', views.TeacherSubjectList.as_view()),

    url(r'^set_subjects/(?P<teacher>[\w.@+-]+)/$', views.set_subjects, name='set_subjects'),

    url(r'^unset_subjects/(?P<teacher>[\w.@+-]+)/$', views.unset_subjects, name='unset_subjects'),

    url(r'^add_teacher/$', views.add_teacher, name='add_teacher'),

    url(r'^teacher_list/(?P<school_id>\w+)/$', views.TeacherList.as_view()),

    url(r'^whether_class_teacher/(?P<teacher_id>\w+)/$', views.whether_class_teacher, name='whether_class_teacher'),

    url(r'^whether_class_teacher2/(?P<teacher>[\w.@+-]+)/$', views.whether_class_teacher2),

    url(r'^delete_teacher/$', views.delete_teacher, name='delete_teacher'),

    url(r'^update_teacher/$', views.update_teacher, name='update_teacher'),

    url(r'^set_class_teacher/$', views.SetClassTeacher.as_view(), name='set_class_teacher'),

    url(r'^download_class_teacher_list/$', views.ClassTeacherList.as_view(), name='download_class_teacher_list'),

    url(r'^retrieve_attendance/$', views.TheTeacherAttendance1.as_view(), name='retrieve_attendance1'),

    url(r'^retrieve_attendance/(?P<school_id>\w+)/(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/$',
        views.TheTeacherAttendance.as_view(), name='retrieve_attendance'),

    url(r'^process_attendance/(?P<school_id>\w+)/$', views.TheTeacherAttendance1.as_view(), name='process_attendance'),

    url(r'^process_attendance/(?P<school_id>\w+)/(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/$',
        views.TheTeacherAttendance.as_view(), name='process_attendance'),

    url(r'^message_list/(?P<teacher>[\w.@+-]+)/$', views.TeacherMessageList.as_view(), name='message_list'),

    url(r'^receivers_list/(?P<key>\w+)/$', views.MessageReceiversList.as_view(), name='receivers_list'),

    url(r'^circulars/(?P<teacher>[\w.@+-]+)/(?P<sender_type>\w+)/$', views.CircularList.as_view(),
        name='circular_list'),

    url(r'^get_class_teacher/$', views.GetClassTeacher.as_view(), name='get_class_teacher'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
