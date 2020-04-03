import json
import urllib2

from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from academics.models import Class, Section, Subject
from authentication.views import JSONResponse
from lectures.models import Lecture
from lectures.serializers import LectureSerializer
from operations import sms
from setup.models import School, GlobalConf
from student.models import Student
from teacher.models import Teacher


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  #


class TeacherLectures(generics.ListAPIView):
    serializer_class = LectureSerializer

    def get_queryset(self):
        user = self.kwargs['teacher']
        teacher = Teacher.objects.get(email=user)
        print('retrieving lectures shared by %s' % teacher)
        q = Lecture.objects.filter(teacher=teacher)
        return q


class StudentLectures(generics.ListAPIView):
    serializer_class = LectureSerializer

    def get_queryset(self):
        user = self.kwargs['student']
        student = Student.objects.get(pk=user)
        the_class = student.current_class
        q = Lecture.objects.filter(the_class=the_class)
        return q


class ShareLecture(generics.ListCreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def post(self, request, *args, **kwargs):
        message_type = 'Share Lecture'
        context_dict = {
            'message_type': message_type
        }

        school_id = request.POST.get('school_id')
        school = School.objects.get(id=school_id)
        teacher_email = request.POST.get('teacher')
        teacher = Teacher.objects.get(email=teacher_email)
        print('teacher = %s' % teacher)
        print('school = %s' % school)
        standard = request.POST.get('the_class')
        the_class = Class.objects.get(school=school, standard=standard)
        print('the_class = %s' % the_class)

        sec = request.POST.get('section')
        print('sec = %s' % sec)
        if sec != '':
            section = Section.objects.get(school=school, section=sec)
            print('section = %s' % section)
        all_sections = request.POST.get('all_sections')
        print(all_sections)

        sub = request.POST.get('subject')
        subject = Subject.objects.get(school=school, subject_name=sub)
        print('subject = %s' % subject)
        youtube_link = request.POST.get('youtube_link')
        print('youtube_link = %s' % youtube_link)
        lesson_topic = request.POST.get('lesson_topic')
        print('lesson_topic = %s' % lesson_topic)
        try:
            lecture = Lecture(teacher=teacher, the_class=the_class, subject=subject,
                              topic=lesson_topic, youtube_link=youtube_link)
            lecture.save()
        except Exception as e:
            print('exception 29032020-A from lecture views.py %s %s' % (e.message, type(e)))
            print('failed in creating lecture record')

        file_included = request.POST.get('file_included')
        print('file_included = %s' % file_included)

        if file_included == 'true' or file_included == 'yes':
            include_link = True
            doc_file = request.FILES['file']
            print(type(doc_file))
            print('doc_file = %s' % doc_file)
            print(doc_file)
            file_name = request.POST.get('file_name').replace(' ', '_')
            # long_link = 'https://storage.cloud.google.com/classup/classup2/media/prod/image_video/%s' % \
            #             image_name.replace('@', '')
            long_link = 'https://classup2.s3.us-east-2.amazonaws.com/media/prod/image_video/%s' % \
                        file_name.replace('@', '')
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
            except Exception as e:
                print('exception 14122019-B-A from lecture views.py %s %s' % (e.message, type(e)))
                print('failed to generate short link  for the lesson doc uploaded by %s' % teacher)

            try:
                print('doc_file = ')
                print(doc_file)
                lecture.pdf_link = short_link
                lecture.doc_file = doc_file
                lecture.save()
            except Exception as e:
                print('exception 29032020-B from lecture views.py %s %s' % (e.message, type(e)))
                print('error in saving document pdf')

        if all_sections == 'true' or all_sections == 'yes':
            print('this lecture to be shared with all sections of class %s' % the_class)
            students = Student.objects.filter(current_class=the_class, active_status=True)
        else:
            print('this lecture to be shared with class %s-%s' % (the_class, section))
            students = Student.objects.filter(current_class=the_class, current_section=section, active_status=True)

        for student in students:
            message = 'Dear %s, class %s %s %s lecture shared. Link:  %s ' % \
                      (student, standard, sub, lesson_topic, youtube_link)
            if file_included == 'true' or file_included == 'yes':
                message += '  Assignment link: %s' % short_link
            print(message)
            p = student.parent
            m1 = p.parent_mobile1
            sms.send_sms1(school, teacher_email, m1, message, message_type)
        return JSONResponse(context_dict, status=200)
