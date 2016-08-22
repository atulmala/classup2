import json

from django.shortcuts import render

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from academics.models import Subject

# Create your views here.

from rest_framework import generics

from .models import Teacher
from academics.models import TeacherSubjects
from .serializers import TeacherSubjectSerializer


class TeacherSubjectList(generics.ListCreateAPIView):
    serializer_class = TeacherSubjectSerializer

    def get_queryset(self):
        t = self.kwargs['teacher']

        the_teacher = Teacher.objects.get(email=t)

        q = TeacherSubjects.objects.filter(teacher=the_teacher).order_by('subject__subject_sequence')

        return q


@csrf_exempt
def set_subjects(request, teacher):
    print ('request.body=')
    if request.method == 'POST':
        t = Teacher.objects.get(email=teacher)
        print (t)
        print ('request.body=')
        print (request.body)

        data = json.loads(request.body)
        print ('data=')
        print (data)

        for key in data:
            print('key=' + key)
            subject = data[key]
            print('subject=' + subject)
            print ('now trying to extract subject')
            try:
                s = Subject.objects.get(subject_code=subject)
            except Exception as e:
                    print('unable to retrieve subject')
                    print ('Exception = %s (%s)' % (e.message, type(e)))

            print ('now trying to set teacher subject')

            try:
                ts = TeacherSubjects.objects.get(teacher=t, subject=s)
                if ts:
                    print('subject ' + s.subject_name + ' has already been selected by teacher '
                          + t.first_name + ' ' + t.last_name)
                    pass

            except Exception as e:
                print('now setting subject ' + s.subject_name + ' for teacher ' + t.first_name + ' ' + t.last_name)
                ts = TeacherSubjects(teacher=t, subject=s)
                try:
                    ts.save()
                    print('successfully set subject ' + s.subject_name +
                          ' for teacher ' + t.first_name + ' ' + t.last_name)
                except Exception as e:
                    print('unable to set subject ' + s.subject_name +
                          ' for teacher ' + t.first_name + ' ' + t.last_name)
                    print ('Exception = %s (%s)' % (e.message, type(e)))

    return HttpResponse('OK')


@csrf_exempt
def unset_subjects(request, teacher):
    print ('request.body=')
    if request.method == 'POST':
        t = Teacher.objects.get(email=teacher)
        print (t)
        print ('request.body=')
        print (request.body)

        data = json.loads(request.body)
        print ('data=')
        print (data)

        for key in data:
            print('key=' + key)
            subject = data[key]
            print('subject=' + subject)
            print ('now trying to extract subject')
            try:
                s = Subject.objects.get(subject_code=subject)
            except Exception as e:
                    print('unable to retrieve subject')
                    print ('Exception = %s (%s)' % (e.message, type(e)))

            print ('now trying to set teacher subject')

            try:
                ts = TeacherSubjects.objects.get(teacher=t, subject=s)
                if ts:
                    print('subject ' + s.subject_name + ' was set for this teacher '
                            + t.first_name + ' ' + t.last_name + '. This will now be deleted')
                    ts.delete()

            except Exception as e:
                print('subject ' + s.subject_name + ' was not set for teacher ' + t.first_name + ' ' + t.last_name)
                print ('Exception = %s (%s)' % (e.message, type(e)))
                pass

    return HttpResponse('OK')



