import os

from django.shortcuts import render
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from teacher.models import Teacher
from student.models import Student
from .models import ImageVideo
from .serializers import ImageVideoSerializer

from authentication.views import JSONResponse, log_entry


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


class ImageVideoList(generics.ListCreateAPIView):
    serializer_class = ImageVideoSerializer

    def get_queryset(self):
        user = self.kwargs['user']

        try:
            teacher = Teacher.objects.get(email=user)
            print('will now try to retrieve the HWs created by %s' % teacher)
            q = ImageVideo.objects.filter(teacher=teacher).order_by('due_date')
            print('query retrieved successfully for HW list of %s = ' % teacher)
            print(q)

            try:
                action = 'Retrieving HW list for %s' % teacher
                log_entry(teacher.email, action, 'Normal', True)
            except Exception as e:
                print('unable to crete logbook entry')
                print ('Exception 504 from academics views.py %s %s' % (e.message, type(e)))
            print('now returning the query retrieved successfully for HW list of %s ' % t)
            return q
        except Exception as e:
            print('Exception 350 from academics view.py %s %s' % (e.message, type(e)))
            print('We need to retrieve the HW list for student')
            try:
                student = Student.objects.get(pk=user)
                school = student.school
                the_class = student.current_class
                section = student.current_section
                q = ImageVideo.objects.filter(the_class=the_class.standard, section=section.section)
                try:
                    action = 'Retrieving HW list for ' + student.fist_name + ' ' + student.last_name
                    parent_mobile = student.parent.parent_mobile1
                    log_entry(parent_mobile, action, 'Normal', True)
                except Exception as e:
                    print('unable to crete logbook entry')
                    print ('Exception 505 from academics views.py %s %s' % (e.message, type(e)))
                return q
            except Exception as e:
                print ('Exception 360 from academics views.py %s %s' % (e.message, type(e)))
                print('could not retrieve student with id %s' % user)


