from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

import views

urlpatterns = [
    url(r'^de_dup/$', views.DeDup.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
