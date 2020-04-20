from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

import views

urlpatterns = [
    url(r'^create_online_test/(?P<school_id>[\w.@+-]+)/$',
        views.CreateOnlineTest.as_view(), name='create_online_test'),

    url(r'^get_online_test/(?P<id>[\w.@+-]+)/$', views.GetOnlineTest.as_view(), name='get_online_test'),

    url(r'^get_online_questions/(?P<test_id>[\w.@+-]+)/$', views.GetOnlineQuestion.as_view(),
        name='get_online_questions')
]

urlpatterns = format_suffix_patterns(urlpatterns)