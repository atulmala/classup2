from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

import views

urlpatterns = [
    url(r'^share_lecture/', views.ShareLecture.as_view(), name='share_lecture'),
    url(r'^get_teacher_lectures/(?P<teacher>[\w.@+-]+)/$',
        views.TeacherLectures.as_view(), name='get_teacher_lectures'),
    url(r'^get_student_lectures/(?P<student>[\w.@+-]+)',
        views.StudentLectures.as_view(), name='get_student_lectures'),
    url(r'^delete_lecture/(?P<id>[\w.@+-]+)', views.DeleteLecture.as_view(), name='delete_lecture')
]

urlpatterns = format_suffix_patterns(urlpatterns)