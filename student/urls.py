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

                       url(r'download_student_list/$', views.StudentListDownload.as_view(),
                           name='download_student_list'),

                       url(r'mid_term_admission/$', views.MidTermAdmission.as_view(), name='mid_term_admission'),
                       url(r'not_promoted/$', views.NotPromoted.as_view(), name='not_promoted'),
                       url(r'promote_students/$', views.StudentPromotion.as_view(), name='promote_students'),
                       url(r'parent_inquiry/$', views.ParentInquiry.as_view(), name='parent_inquiry'),
                       url(r'add_student_web/$', views.AddStudent.as_view(), name='add_student_web'),
                       url(r'update_student_web/$', views.UpdateStudent.as_view(), name='update_student_web'),
                       url(r'single_student_details/(?P<school_id>\w+)/$', views.SingleStudentDetails.as_view(),
                           name='single_student_details'),
                       url(r'^demote_students/$', views.StudentDemotion.as_view(), name='demotes_students')
            )
