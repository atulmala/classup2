__author__ = 'atulgupta'

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from pic_share import views

urlpatterns = [
    url(r'^get_pic_video_list_teacher/(?P<teacher>[\w.@+-]+)/$', views.ImageVideoList.as_view(),
        name='get_pic_video_list_teacher'),
    url(r'^get_pic_video_list_student/(?P<teacher>[\w.@+-]+)/$', views.ImageVideoList.as_view(),
        name='get_pic_video_list_student'),
    url(r'upload_pic/$', views.UploadImage.as_view(), name='upload_pic'),
    url(r'delete_media/(?P<image_id>[\w\ ]+)/$', views.DeleteMedia.as_view(), name='delete_media'),
]

urlpatterns = format_suffix_patterns(urlpatterns)