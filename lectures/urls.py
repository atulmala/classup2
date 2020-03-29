from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

import views

urlpatterns = [
    url(r'^share_lecture/', views.ShareLecture.as_view(), name='share_lecture'),
]

urlpatterns = format_suffix_patterns(urlpatterns)