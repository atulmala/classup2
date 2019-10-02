from django.conf.urls import url, patterns

from student import views as student_view
from . import views


urlpatterns = patterns(
    '',
    url(r'^setup_third_lang/$', views.setup_third_lang, name='setup_third_lang'),

    url(r'^setup_scheme/$', views.setup_scheme, name='setup_scheme'),

    url(r'^term_results/$', views.term_results, name='term results'),

    url(r'^term_results/student/get_students/(?P<school_id>\w+)/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/$',
        student_view.StudentList.as_view()),

    url(r'^term_results/academics/prepare_results/(?P<school_id>\w+)/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/$',
        views.prepare_results, name='prepare_results'),

    url (r'^setup_higher_class_subject_mapping/$', views.setup_higher_class_subject_mapping,
         name='setup_higher_class_subject_mapping'),

    url (r'result_sheet/$', views.ResultSheet.as_view(), name='result_sheet'),
    url(r'upload_marks/$', views.UploadMarks.as_view(), name='upload_marks'),
)
