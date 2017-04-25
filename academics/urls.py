__author__ = 'atulgupta'

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from academics import views


urlpatterns = [
    url(r'^class_list/(?P<school_id>\w+)/$', views.ClassList.as_view()),

    url(r'^section_list/(?P<school_id>\w+)/$', views.SectionList.as_view()),

    url(r'^subject_list/(?P<school_id>\w+)/$', views.SubjectList.as_view()),

    url(r'^completed_test_list/(?P<teacher>[\w.@+-]+)/$', views.CompletedTestList.as_view()),

    url(r'^pending_test_list/(?P<teacher>[\w.@+-]+)/$', views.PendingTestList.as_view()),

    url(r'^create_test/(?P<school_id>\w+)/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/'
        r'(?P<subject>[\w\ ]+)/(?P<teacher>[\w.@+-]+)'
        r'/(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/'
        r'(?P<max_marks>\w+)/(?P<pass_marks>\w+)/(?P<grade_based>\w+)/(?P<comments>[\w\ ]+)/$',
        views.create_test, name='create_test'),

    url(r'^class_section_for_test/(?P<id>\w+)/$', views.ClassSectionForTest.as_view()),

    url(r'^get_test_marks_list/(?P<test_id>\w+)/$', views.MarksListForTest.as_view()),

    url(r'^save_marks/$', views.save_marks, name='save_marks'),

    url(r'^submit_marks/(?P<school_id>\w+)/$', views.submit_marks, name='submit_marks'),

    url(r'get_working_days1/', views.get_working_days1, name='get_working_days1'),

    url(r'get_attendance_summary/', views.get_attendance_summary, name='get_attendance_summary'),

    url(r'delete_test/(?P<test_id>\w+)/$', views.delete_test, name='delete_test'),

    url(r'delete_hw/(?P<hw_id>\w+)$', views.delete_hw, name='delete_hw'),

    url(r'get_test_type/(?P<test_id>\w+)/$', views.TestType.as_view()),

    url(r'^get_exam_list/(?P<student_id>[\w.@+-]+)/$', views.ExamList.as_view(), name='get_exam_list'),

    url(r'^create_hw/', views.create_hw, name='create_hw'),

    url(r'^retrieve_hw/(?P<user>[\w.@+-]+)/$', views.HWList.as_view(), name='retrieve_hw'),

    url(r'^get_hw_image/(?P<hw_id>\w+)/$', views.get_hw_image, name='get_hw_image'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
