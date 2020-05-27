__author__ = 'atulmala'

from django.conf.urls import url
from setup import views

urlpatterns = [
    url('^$', views.setup_index, name='setup_index'),
    url(r'^upload_students/$', views.setup_students, name='upload_students'),
    url(r'^upload_teachers/$', views.setup_teachers, name='upload_teachers'),
    url(r'^upload_classes/$', views.setup_classes, name='upload_classes'),
    url(r'^upload_sections/$', views.setup_sections, name='upload_sections'),
    url(r'^upload_subjects/$', views.setup_subjects, name='upload_subjects'),

    url(r'^upload_classteacher_details/$', views.setup_class_teacher,
        name='setup_class_teacher'),
    url(r'^upload_exam/$', views.setup_exam, name='upload_exam'),
    url(r'^bus_attendance_enabled/(?P<school_id>\w+)/$',
        views.ConfigurationList.as_view(), name='bus_attendance_enabled'),
    url(r'^check_reg_no/$', views.check_reg_no, name='check_reg_no'),
    url(r'^add_student/$', views.add_student, name='add_student'),
    url(r'^update_student/$', views.update_student, name='update_student'),
    url(r'^delete_student/$', views.delete_stuednt, name='delete_student'),
    url(r'^upload_dob/$', views.setup_dob, name='setup dob'),
]
