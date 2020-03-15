from django.conf.urls import url, patterns

from student import views as student_view
from . import views

urlpatterns = patterns(
    '',
    url(r'^setup_third_lang/$', views.setup_third_lang, name='setup_third_lang'),

    url(r'^setup_scheme/$', views.setup_scheme, name='setup_scheme'),

    url(r'^term_results/student/get_students/(?P<school_id>\w+)/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/$',
        student_view.StudentList.as_view()),

    url(r'^marksheet/(?P<school_id>\w+)/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/$',
        views.GenerateMarksheet.as_view(), name='marksheet'),

    url(r'^setup_higher_class_subject_mapping/$', views.setup_higher_class_subject_mapping,
         name='setup_higher_class_subject_mapping'),

    url (r'result_sheet/$', views.ResultAnalysisSheet.as_view(), name='result_sheet'),
    url(r'upload_marks/$', views.UploadMarks.as_view(), name='upload_marks'),
    url(r'schedule_test/$', views.ScheduleTest.as_view(), name='schedule_test'),
    url(r'get_wings/(?P<school_id>\w+)/$', views.GetWings.as_view(), name='get_wings'),
    url(r'get_tests/$', views.TestList.as_view(), name='get_tests'),
    url(r'^get_test_marks_list/$', views.MarksListForTest.as_view()),
    url(r'^initialize_promotion_list/$', views.InitializePromotionList.as_view(), name='initialize_promotion_list'),
    url(r'^get_promotion_list/$', views.GetPromotionList.as_view(), name='get_promotion_list'),
    url(r'^process_promotion/$', views.ProcessPromotion.as_view(), name='process_promotion'),
    url(r'^get_student_marks/$', views.StudentMarks.as_view(), name='get_student_marks'),
    url(r'^get_promotion_excel/$', views.PromotionReport.as_view(), name='get_promotion_excel'),
    url(r'^cbse_mapping/$', views.CBSEMapping.as_view(), name='cbse_mapping'),
    url(r'^generate_cbse_sheet/$', views.GenerateCBSESheet.as_view(), name='generate_cbse_sheet'),
    url(r'^unscheuled_test_list/$', views.UnscheduledTestList.as_view(), name='unscheuled_test_list'),
    url(r'^detain_list/$', views.DetainList.as_view(), name='detain_list'),
    url(r'^student_subject_list/$', views.StudentSubjects.as_view(), name='student_subject_list'),
)