from django.conf.urls import url

import views

urlpatterns = [
    url(r'^create_online_test/(?P<school_id>[\w.@+-]+)/$',
        views.CreateOnlineTest.as_view(), name='create_online_test'),

    url(r'^get_online_test/(?P<id>[\w.@+-]+)/$', views.GetOnlineTest.as_view(),
        name='get_online_test'),

    url(r'^whether_attempted/(?P<student_id>[\w.@+-]+)/(?P<test_id>[\w.@+-]+)/$',
        views.WhetherAttempted.as_view(), name='whether_attempted'),

    url(r'^mark_attempted/(?P<student_id>[\w.@+-]+)/(?P<test_id>[\w.@+-]+)/$',
        views.MarkAttempted.as_view(), name='mark_attempted'),

    url(r'^get_online_questions/(?P<test_id>[\w.@+-]+)/$', views.GetOnlineQuestion.as_view(),
        name='get_online_questions'),

    url(r'^submit_answers/$', views.SubmitAnswer.as_view(), name='submit_answers'),

    url(r'^mark_answer/$', views.MarkAnswer.as_view(), name='mark_answer'),

    url(r'^generate_answer_sheet/$',views.GenerateAnswerSheet.as_view(), name='generate_answer_sheet'),

    url(r'^share_answer_sheet/$',views.ShareAnswerSheet.as_view(), name='share_answer_sheet'),

    url(r'^get_failed_attempts', views.FailedAttempts.as_view(), name='get_failed_attempts'),
]