from django.conf.urls import url

from bus_attendance import views

urlpatterns = [
    url(r'^retrieve_bus_routs/(?P<school_id>\w+)/$', views.RoutList.as_view()),
    url(r'^retrieve_bus_stops/(?P<school_id>\w+)/(?P<rout>[\w.@+-]+)/', views.StopListForRout.as_view(),
        name='stop_list'),
    url(r'^setup_routs/', views.setup_routs),
    url(r'^setup_bus_stops/', views.setup_bus_stops),
    url(r'^setup_student_routs/', views.student_bus_rout),

    url(r'^list_rout_students1/(?P<school_id>\w+)/(?P<rout>[\w.@+-]+)/(?P<bus_stop>[\w\ .@+-]+)/',
        views.StudentListForRout1.as_view()),

    url(r'^bus_attendance_taken/(?P<school_id>\w+)/(?P<rout>[\w.@+-]+)/(?P<t>[\w.@+-]+)/'
        r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/(?P<teacher>[\w.@+-]+)/$',
        views.bus_attendance_taken, name='bus_attendance_taken'),

    url(r'^retrieve_bus_attendance/(?P<school_id>\w+)/(?P<rout>[\w.@+-]+)/(?P<type>[\w.@+-]+)/'
        r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/$',
        views.BusAttendanceList.as_view(), name='bus_attendance_list'),

    url(r'^delete_bus_attendance1/(?P<att_type>[\w.@+-]+)/'
        r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/$', views.delete_bus_attendance1, name='delete_bus_attendance1'),

    url(r'^process_bus_attendance1/(?P<att_type>[\w.@+-]+)/'
        r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/(?P<teacher>[\w.@+-]+)/$',
        views.process_bus_attendance1, name='process_bus_attendance1'),

    url(r'^report_delay/', views.report_delay, name='report_delay'),

    url(r'^attendance_taken_earlier/(?P<school_id>\w+)/(?P<rout>[\w.@+-]+)/'
        r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/$', views.attendance_taken_earlier, name='attendance_taken_earlier'),
]
