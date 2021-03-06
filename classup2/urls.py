"""classup2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from django.conf.urls import include, url
from django.contrib import admin
from classup2 import settings

urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('authentication.urls')),
    url(r'^setup/', include('setup.urls')),
    url(r'^academics/', include('academics.urls')),
    url(r'^student/', include('student.urls')),
    url(r'^operations/', include('operations.urls')),
    url(r'^attendance/', include('attendance.urls')),
    url(r'^teachers/', include('teacher.urls')),
    url(r'^bus_attendance/', include('bus_attendance.urls')),
    url(r'^parents/', include('parents.urls')),
    url(r'^exam/', include('exam.urls')),
    url(r'^time_table/', include('time_table.urls')),
    url(r'^activity_groups/', include('activity_groups.urls')),
    url(r'^erp/', include('erp.urls')),
    url(r'^fee_processing/', include('fee_processing.urls')),
    url(r'^maintenance/', include('maintenance.urls')),
    url(r'^pic_share/', include('pic_share.urls')),
    url(r'^analytics/', include('analytics.urls')),
    url(r'^lectures/', include('lectures.urls')),
    url(r'^online_test/', include('online_test.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
