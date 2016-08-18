from parents import views
from django.conf.urls import url, patterns

urlpatterns = patterns('',
                       url(r'^retrieve_stu_att_summary/', views.retrieve_stu_att_summary),
                       url(r'^retrieve_categories/', views.CategoryList.as_view()),
                       url(r'^submit_parents_communication/', views.submit_parents_communication),
                       url(r'^retrieve_student_subjects/', views.retrieve_student_subjects),
                       url(r'^retrieve_stu_sub_marks_history/(?P<subject>[\w\ ]+)/$',
                           views.retrieve_stu_sub_marks_history),
                       url(r'^get_exam_result/(?P<student_id>[\w\ ]+)/(?P<exam_id>[\w\ ]+)/$', views.get_exam_result),
                       )
