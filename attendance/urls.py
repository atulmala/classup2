__author__ = 'atulgupta'

from django.conf.urls import url, patterns

from attendance import views


urlpatterns = patterns('',
        url(r'^retrieve/(?P<school_id>\w+)/(?P<class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/(?P<subject>[\w\ ]+)/'
            r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/$',
            views.AttendanceList.as_view()),

        url(r'^update/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/(?P<subject>[\w\ ]+)/'
            r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/(?P<id>\w+)/(?P<teacher>[\w.@+-]+)/$',
            views.process_attendance, name='process_attendance'),

        url(r'^update1/(?P<school_id>\w+)/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/(?P<subject>[\w\ ]+)/'
            r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/(?P<teacher>[\w.@+-]+)/$',
            views.process_attendance1, name='process_attendance1'),

        url(r'^delete/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/(?P<subject>[\w\ ]+)/'
            r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/(?P<id>\w+)/$',
            views.delete_attendance, name='delete_attendance'),

        url(r'^delete2/(?P<school_id>\w+)/(?P<the_class>[\w.@+-]+)/(?P<section>[\w.@+-]+)/(?P<subject>[\w\ ]+)/'
            r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/$',
            views.delete_attendance2, name='delete_attendance2'),

        url(r'^attendance_taken/(?P<school_id>\w+)/(?P<the_class>[\w.@+-]+)/'
            r'(?P<section>[\w.@+-]+)/(?P<subject>[\w\ ]+)/'
            r'(?P<d>\w+)/(?P<m>\w+)/(?P<y>\w+)/(?P<teacher>[\w.@+-]+)/$',
            views.attendance_taken, name='attendance_taken'),
        )
