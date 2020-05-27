import os
import json
import base64
import ast
import urllib2
import httplib
import httplib2
import hashlib
import random
import sys
import time

import google.oauth2.credentials
from django.http import HttpResponseBadRequest
import progressbar as pb

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.contrib import xsrfutil
from oauth2client.contrib.django_util.storage import DjangoORMStorage

from googleapiclient.errors import HttpError, ResumableUploadError

from rest_framework import generics
from rest_framework.parsers import FileUploadParser
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect
from django.conf import settings
from django.views.generic.base import View


from setup.models import GlobalConf
from teacher.models import Teacher
from student.models import Student
from academics.models import Class, Section
from operations import sms
from .models import ImageVideo, ShareWithStudents
from .models import CredentialModel
from .serializers import ImageVideoSerializer, SharedWithSerializer

from authentication.views import JSONResponse, log_entry

httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
                            httplib.IncompleteRead, httplib.ImproperConnectionState,
                            httplib.CannotSendRequest, httplib.CannotSendHeader,
                            httplib.ResponseNotReady, httplib.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
CLIENT_SECRETS_FILE = 'client_secrets.json'
SERVICE_ACCOUNT_FILE = 'service_account.json'
YOUTUBE_UPLOAD_SCOPE = ['https://www.googleapis.com/auth/youtube.upload']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
MISSING_CLIENT_SECRETS_MESSAGE = 'client_secrets file missing'
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

flow = flow_from_clientsecrets(
            CLIENT_SECRETS_FILE,
            YOUTUBE_UPLOAD_SCOPE,
            redirect_uri='http://localhost:8000/pic_share/oauth2callback/')


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
            if whole_class == 'false':
                student_list = data['student_list']
                print(student_list)
                print(type(student_list))

                # 29/08/2019 - when comes from Android, the student id list comes as an array. So we need to break it
                # into list. But from iOS, it comes as a proper list. So need not break it
                try:
                    students = ast.literal_eval(student_list)
                    print(students)
                except Exception as e:
                    print('exception 29082019-A from pic_share views.py %s %s' % (e.message, type(e)))
                    print('looks the request has come from iOS, hence no need for ast.literal_eval')
                    students = student_list

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

            # long_link = 'https://storage.cloud.google.com/classup/classup2/media/prod/image_video/%s' % \
            #             image_name.replace('@', '')
            long_link = 'https://classup2.s3.us-east-2.amazonaws.com/media/prod/image_video/%s' % \
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
                req = urllib2.Request(url, headers={'User-Agent': "Magic Browser"})
                response = urllib2.urlopen(req)
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
            q = ImageVideo.objects.filter(teacher=teacher, active_status=True).order_by('-creation_date')
            print('query retrieved successfully for Image Video list of %s = ' % teacher)
            print(q)

            try:
                action = 'Retrieving Image Video list for %s' % teacher
                log_entry(teacher.email, action, 'Normal', True)
            except Exception as e:
                print('unable to crete logbook entry')
                print ('Exception 504 from pic_share views.py %s %s' % (e.message, type(e)))
            print('now returning the query retrieved successfully for Image/Video list of %s ' % teacher)
            return q
        except Exception as e:
            print('Exception 12082019-B from pic_share view.py %s %s' % (e.message, type(e)))
            print('We need to retrieve the Image/Video list for student')
            self.serializer_class = SharedWithSerializer
            try:
                student = Student.objects.get(pk=user)

                q = ShareWithStudents.objects.filter(student=student).order_by('image_video__creation_date')

                return q
            except Exception as e:
                print ('Exception 12082019-A from pic_share views.py %s %s' % (e.message, type(e)))
                print('could not retrieve student with id %s' % user)


class Oauth2CallbackView(View):

    def get(self, request, *args, **kwargs):
        if not xsrfutil.validate_token(
            settings.SECRET_KEY, request.GET.get('state').encode(),
            request.user):
                return HttpResponseBadRequest()
        credential = flow.step2_exchange(request.GET)
        storage = DjangoORMStorage(
            CredentialModel, 'id', request.user.id, 'credential')
        storage.put(credential)
        return redirect('/')


def resumable_upload(insert_request):
    print('inside resume upload')
    response = None
    error = None
    retry = 0

    widgets = ['Uploading: ', pb.Percentage(), ' ', pb.Bar(marker='#', left='[', right=']'), ' ', pb.ETA(), ' ',
               pb.FileTransferSpeed()]  # see docs for other options
    pbar = pb.ProgressBar(widgets=widgets, maxval=1)
    pbar.start()
    while response is None:
        try:
            print "Uploading file..."
            status, response = insert_request.next_chunk()
            if response is None:
                pbar.update(status.progress())
                continue
            if 'id' in response:
                print "Video id '%s' was successfully uploaded." % response['id']
                print('whole response = ')
                print(response)
                status = 'success'
                return status, response['id']
            else:
                print("The upload failed with an unexpected response: %s" % response)
                status = 'failure'
                return status, None

        except ResumableUploadError as e:
            print(("ResumableUploadError e.content:{}".format(e.content)))
            print("to get out of this loop:\nimport sys;sys.exit()")
            import code
            code.interact(local=locals())
        except HttpError, e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                     e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS, e:
            error = "A retriable error occurred: %s" % e
        except Exception as e:
            print('exception 04092019-B from pic_share views.py %s %s' % (e.message, type(e)))
            print('failed to upload video')

        if error is not None:
            print error
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print "Sleeping %f seconds and then retrying..." % sleep_seconds
            time.sleep(sleep_seconds)


class UploadVideo(generics.ListCreateAPIView):
    print('inside upload video')
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    parser_classes = (FileUploadParser,)

    def get(self, request, *args, **kwargs):
        print('inside setting up credentials')
        print('user id = ')
        print(request.user.id)
        storage = DjangoORMStorage(
            CredentialModel, 'id', request.user.id, 'credential')
        credential = storage.get()
        print('credentials = ')
        print(credential)

        if credential is None or credential.invalid == True:
            print('credential found to be invalid or None')
            flow.params['state'] = xsrfutil.generate_token(
                settings.SECRET_KEY, request.user)
            print('state = ')
            print(flow.params['state'])
            authorize_url = flow.step1_get_authorize_url()
            print('authorize_url = ')
            print(authorize_url)
            return redirect(authorize_url)
        else:
            print('credential does exist and it is valid too!')
        return redirect('/')

    def post(self, request, *args, **kwargs):
        print('user id in post request = ')
        data = request.POST
        print(data)
        context_dict = {

        }
        try:
            storage = DjangoORMStorage(
                CredentialModel, 'id', 1, 'credential')

            credential = storage.get()
            print('credential = ')
            print(credential)
            if credential is None or credential.invalid == True:
                print('credential found to be invalid or None')
            else:
                print('credentials are found to be valid')

            client = build('youtube', 'v3', http=credential.authorize(httplib2.Http()))
            print('client = ')
            print(client)

            params = (request.POST['params'])
            print(params)
            data = json.loads(params)
            print('Video sharing process started')
            teacher = data['teacher']
            t = Teacher.objects.get(email=teacher)
            print (t)
            print(teacher)
            the_class = data['the_class']
            print(the_class)
            c = Class.objects.get(school=t.school, standard=the_class)
            print (c)
            section = data['section']
            print(section)
            s = Section.objects.get(school=t.school, section=section)
            print (s)
            description = data['description']
            whole_class = data['whole_class']
            print('whole class = %s' % whole_class)
            if whole_class == 'false':
                student_list = data['student_list']
                print(student_list)
                print(type(student_list))

                # 29/08/2019 - when comes from Android, the student id list comes as an array. So we need to break it
                # into list. But from iOS, it comes as a proper list. So need not break it
                try:
                    students = ast.literal_eval(student_list)
                    print(students)
                except Exception as e:
                    print('exception 04092019-A from pic_share views.py %s %s' % (e.message, type(e)))
                    print('looks the request has come from iOS, hence no need for ast.literal_eval')
                    students = student_list
            print('will now save the video received in local storage temporarily')
            print(request.FILES)
            up_file = request.FILES['video']
            folder = 'uploaded_videos'
            fs = FileSystemStorage(location=folder)  # defaults to   MEDIA_ROOT
            filename = fs.save(up_file.name, up_file)
            print('file successfully saved locally %s' % filename)

            body = dict(
                snippet=dict(
                    title=description,
                    description=description,
                    tags=['ClassUp'],
                    categoryId=22
                ),
                status=dict(
                    privacyStatus='private'
                )
            )
            file_location = '%s/%s' % (folder, filename)
            insert_request = client.videos().insert(part=','.join(body.keys()), body=body,
                media_body=MediaFileUpload(
                    file_location,
                    #chunksize=-1,
                    chunksize = 5 * 1024 * 1024,
                    resumable=True)
                )
            status, video_id = resumable_upload(insert_request)
            if status == 'success':
                link = ''
        except Exception as e:
            print('exception 02092019-A from pic_share views.py %s %s' % (e.message, type(e)))
            print('failed to upload to YouTube')

        return JSONResponse(context_dict, status=200)

