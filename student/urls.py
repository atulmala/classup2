__author__ = 'atulgupta'

from django.conf.urls import url, patterns

from student import views


urlpatterns = patterns('',
                       url(r'^list/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/$',
                           views.StudentList.as_view()),
                       url(r'^student_list_for_test/(?P<test_id>\w+)/$',
                           views.StudentListForTest.as_view()),
                       url(r'student_list_for_parents/(?P<parent_mobile>\w+)/$',
                           views.StudentListForParent.as_view()),
                       )
