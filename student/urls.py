__author__ = 'atulgupta'

from django.conf.urls import url, patterns

from student import views


urlpatterns = patterns('',
                        url(r'^list/(?P<school_id>\w+)/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/$',
                           views.StudentList.as_view()),
                        url(r'^student_list_for_test/(?P<test_id>\w+)/$', views.StudentListForTest.as_view()),
                        url(r'student_list_for_parents/(?P<parent_mobile>\w+)/$', views.StudentListForParent.as_view()),
                        url(r'get_parent/(?P<student_id>\w+)/$', views.get_parent, name='get_parent'),
                        url(r'get_student_detail/(?P<student_id>\w+)/$',
                            views.get_student_detail, name='get_student_detail'),
                       )
