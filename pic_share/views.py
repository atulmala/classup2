import os
import json
import base64

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from django.core.files.base import ContentFile

from teacher.models import Teacher
from student.models import Student
from academics.models import Class, Section
from .models import ImageVideo, ShareWithStudents
from .serializers import ImageVideoSerializer

from authentication.views import JSONResponse, log_entry


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


class UploadImage(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        context_dict['header'] = 'Share Image'
        try:
            data = json.loads(request.body)

            print('Image sharing process started')
            teacher = data['teacher']
            t = Teacher.objects.get(email=teacher)
            print (t)
            print(teacher)
            the_class = data['class']
            print(the_class)
            c = Class.objects.get(school=t.school, standard=the_class)
            print (c)
            section = data['section']
            print(section)
            s = Section.objects.get(school=t.school, section=section)
            print (s)
            whole_class = data['whole_class']
            print('whole class = %s' % whole_class)

            image_name = data['image_name']
            print(image_name)

            image = data['image']

            image_file = ContentFile(base64.b64decode(image), name=image_name)

            # save the home work
            image_video = ImageVideo()
            image_video.location = image_file
            image_video.teacher = t
            image_video.the_class = c
            image_video.section = s

            try:
                image_video.save()

                # now update with the SharedWith table
                if whole_class == 'true':
                    print('this image/video is shared with whole class %s-%s' % (the_class, section))
                    students = Student.objects.filter(current_class=c, current_section=s)
                    for student in students:
                        try:
                            shared = ShareWithStudents(image_video=image_video,
                                                       student=student, the_class=c, section=s)
                            shared.save()
                            print('saved the SharedWithStudent for %s of %s-%s' % (student, the_class, section))
                        except Exception as e:
                            print('exception 01082019-A from pic_share views.py %s %s' % (e.message, type(e)))
                            print('failed to save SharedWithStudent object')
                context_dict['status'] = 'success'
                print(image_video.location)
                try:
                    action = 'uploading image for %s-%s teacher %s' % (the_class, section, t)
                    print(action)
                    log_entry(teacher, action, 'Normal', True)
                except Exception as e:
                    print('unable to crete logbook entry')
                    print ('Exception 31072019-A from pic_share views.py %s %s' % (e.message, type(e)))
                return JSONResponse(context_dict, status=200)
            except Exception as e:
                print('Exception 31072019-B from pic_share views.py = %s (%s)' % (e.message, type(e)))
                print('error while trying to save the image/video uploaded by %s' % t)
                context_dict['status'] = 'failed'
                return JSONResponse(context_dict, status=201)

        except Exception as e:
            print('failed to get the POST data for create hw')
            print('Exception 300 from academics views.py = %s (%s)' % (e.message, type(e)))
            context_dict['status'] = 'failed'
            return JSONResponse(context_dict, status=201)


class ImageVideoList(generics.ListCreateAPIView):
    serializer_class = ImageVideoSerializer

    def get_queryset(self):
        user = self.kwargs['teacher']

        try:
            teacher = Teacher.objects.get(email=user)
            print('will now try to retrieve the Images Video created by %s' % teacher)
            q = ImageVideo.objects.filter(teacher=teacher).order_by('due_date')
            print('query retrieved successfully for Image Video list of %s = ' % teacher)
            print(q)

            try:
                action = 'Retrieving Image Video list for %s' % teacher
                log_entry(teacher.email, action, 'Normal', True)
            except Exception as e:
                print('unable to crete logbook entry')
                print ('Exception 504 from academics views.py %s %s' % (e.message, type(e)))
            print('now returning the query retrieved successfully for HW list of %s ' % teacher)
            return q
        except Exception as e:
            print('Exception 350 from academics view.py %s %s' % (e.message, type(e)))
            print('We need to retrieve the HW list for student')
            try:
                student = Student.objects.get(pk=user)
                the_class = student.current_class
                section = student.current_section
                q = ImageVideo.objects.filter(the_class=the_class.standard, section=section.section)
                try:
                    action = 'Retrieving Image Video list for ' + student.fist_name + ' ' + student.last_name
                    parent_mobile = student.parent.parent_mobile1
                    log_entry(parent_mobile, action, 'Normal', True)
                except Exception as e:
                    print('unable to crete logbook entry')
                    print ('Exception 505 from academics views.py %s %s' % (e.message, type(e)))
                return q
            except Exception as e:
                print ('Exception 360 from academics views.py %s %s' % (e.message, type(e)))
                print('could not retrieve student with id %s' % user)