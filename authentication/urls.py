__author__ = 'atulmala'

from authentication import views
from django.conf.urls import url, patterns
from django.views.decorators.csrf import csrf_exempt

from .views import LogEntry

urlpatterns = patterns('',
    url('^$', views.auth_login, name='auth_index'),
    url('^auth/login/$', views.auth_login, name='auth_login'),
    url('^logout/$', views.auth_logout, name='auth_logout'),

    url(r'^auth/login1/$', views.auth_login_from_device1, name='login_from_device1'),

    url(r'auth/change_password/$', views.change_password, name="change_password"),
    url(r'auth/forgot_password/$', views.forgot_password, name='forgot_password'),
    url(r'auth/check_subscription/(?P<student_id>\w+)/$', views.check_subscription, name='check_subscription'),
    url(r'auth/map_device_token/$', views.map_device_token, name='map_device_token'),
    url(r'auth/logbook_entry/$', LogEntry.as_view()),
)
