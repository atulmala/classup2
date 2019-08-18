import os
import json
import base64
import ast
import urllib2

from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from django.core.files.base import ContentFile

from setup.models import GlobalConf
from teacher.models import Teacher
from student.models import Student
from academics.models import Class, Section
from operations import sms
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
            print(data)

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
            if whole_class == 'false':
                student_list = data['student_list']
                print(student_list)
                print(type(student_list))
                students = ast.literal_eval(student_list)
                print(students)

            image_name = data['image_name']
            print(image_name)

            image = data['image']
            image_file = ContentFile(base64.b64decode(image), name=image_name.replace('@', ''))

            description = data['description']
            print (description)

            # save the image
            image_video = ImageVideo()
            image_video.location = image_file
            image_video.descrition = description
            image_video.teacher = t
            image_video.the_class = c
            image_video.section = s

            # long_link = 'https://storage.cloud.google.com/classup/classup2/media/dev/image_video/%s' % \
            #             image_name.replace('@', '')
            long_link = 'https://storage.cloud.google.com/classup/classup2/media/prod/image_video/%s' % \
                        image_name.replace('@', '')
            print('long_link = %s' % long_link)
            short_link = long_link

            # prepare short link
            global_conf = GlobalConf.objects.get(pk=1)
            key = global_conf.short_link_api
            url = 'https://cutt.ly/api/api.php?'
            url += 'key=%s&short=%s' % (key, long_link)
            print('url for generating short link = %s' % url)
            try:
                response = urllib2.urlopen(url)
                print('response for generating short link = %s' % response)
                outcome = json.loads(response.read())
                print('ouctome = ')
                print(outcome)
                status = outcome['url']['status']
                print('status = %i' % status)
                if status == 7:
                    short_link = outcome['url']['shortLink']
                    print('short_lint = %s' % short_link)
                    image_video.short_link = short_link
                    # image_video.short_link = short_link
                    # image_video.save()
                # else:
                #     image_video.short_link = long_link
                #     image_video.save()
            except Exception as e:
                print('exception 15082019-A from pic_share views.py %s %s' % (e.message, type(e)))
                print('failed to generate short link  for the image/video uploaded by %s' % t)
                image_video.short_link = 'not available'

            try:
                image_video.save()
                print('saved the image uploaded by %s' % t)

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
                            parent = student.parent.parent_name
                            message = 'Dear %s new pic uploaded. %s. Click %s' % (parent, description, short_link)
                            print(message)
                            sms.send_sms1(student.school, teacher, student.parent.parent_mobile1, message, 'Share Pic')
                        except Exception as e:
                            print('exception 01082019-A from pic_share views.py %s %s' % (e.message, type(e)))
                            print('failed to save SharedWithStudent object')
                else:
                    for an_item in students:
                        try:
                            student = Student.objects.get(pk=an_item)
                            shared = ShareWithStudents(image_video=image_video,
                                                       student=student, the_class=c, section=s)
                            shared.save()
                            print('saved the SharedWithStudent for %s of %s-%s. Now sending sms' % (student, c, s))

                            parent = student.parent.parent_name
                            message = 'Dear %s new pic uploaded. %s. Click %s' % (parent, description, short_link)
                            print(message)
                            sms.send_sms1(student.school, teacher, student.parent.parent_mobile1, message, 'Share Pic')
                        except Exception as e:
                            print('exception 02082019-A from pic_share views.py %s %s' % (e.message, type(e)))
                            print('failed to save SharedWithStudent object')
                context_dict['status'] = 'success'
                context_dict['message'] = 'Media upload successful'
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
                context_dict['message'] = 'error while trying to save the image/video uploaded'
                return JSONResponse(context_dict, status=201)
        except Exception as e:
            print('failed to save image/video')
            print('Exception 02082019-B from pic_share views.py = %s (%s)' % (e.message, type(e)))
            context_dict['status'] = 'failed'
            context_dict['message'] = 'error while trying to save the image/video uploaded'
            return JSONResponse(context_dict, status=201)


class DeleteMedia(generics.DestroyAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def delete(self, request, *args, **kwargs):
        context_dict = {

        }
        image_id = self.kwargs["image_id"]
        try:
            media = ImageVideo.objects.get(id=image_id)
            media.active_status = False
            media.save()
            print('media marked inactive')
            context_dict['message'] = 'Media deleted'
            context_dict['status'] = 'success'
            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('exception 13082019-A from pic_share views.py %s %s' % (e.message, type(e)))
            message = 'failed to delete media. Please try again.'
            context_dict['message'] = message
            context_dict['status'] = 'failed'
            return JSONResponse(context_dict, status=201)


class ImageVideoList(generics.ListCreateAPIView):
    serializer_class = ImageVideoSerializer

    def get_queryset(self):
        user = self.kwargs['teacher']

        try:
            teacher = Teacher.objects.get(email=user)
            print('will now try to retrieve the Images Video created by %s' % teacher)
            q = ImageVideo.objects.filter(teacher=teacher, active_status=True).order_by('creation_date')
            print('query retrieved successfully for Image Video list of %s = ' % teacher)
            print(q)

            try:
                action = 'Retrieving Image Video list for %s' % teacher
                log_entry(teacher.email, action, 'Normal', True)
            except Exception as e:
                print('unable to crete logbook entry')
                print ('Exception 504 from academics views.py %s %s' % (e.message, type(e)))
            print('now returning the query retrieved successfully for Image/Video list of %s ' % teacher)
            return q
        except Exception as e:
            print('Exception 12082019-B from pic_share view.py %s %s' % (e.message, type(e)))
            print('We need to retrieve the Image/Video list for student')
            try:
                student = Student.objects.get(pk=user)
                the_class = student.current_class
                section = student.current_section
                q = ImageVideo.objects.filter(the_class=the_class.standard,
                                              section=section.section, active_status=True).order_by('creation_date')
                try:
                    action = 'Retrieving Image Video list for ' + student.fist_name + ' ' + student.last_name
                    parent_mobile = student.parent.parent_mobile1
                    log_entry(parent_mobile, action, 'Normal', True)
                except Exception as e:
                    print('unable to crete logbook entry')
                    print ('Exception 505 from academics views.py %s %s' % (e.message, type(e)))
                return q
            except Exception as e:
                print ('Exception 12082019-A from pic_share views.py %s %s' % (e.message, type(e)))
                print('could not retrieve student with id %s' % user)