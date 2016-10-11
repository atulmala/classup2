
# Create your views here.

from rest_framework import generics

from setup.models import School
from academics.models import ClassTest
from .models import Student, Parent

from .serializers import StudentSerializer, ParentSerializer

from authentication.views import JSONResponse


class StudentList(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        """
        :return: list of all students based on class and section supplied by the URL
        """
        print (self.request._request)
        print (self.kwargs)

        school_id = self.kwargs['school_id']
        school = School.objects.get(id=school_id)
        the_class = self.kwargs['the_class']
        section = self.kwargs['section']

        q1 = Student.objects.filter(school=school, current_section__section=section,
                                    current_class__standard=the_class, active_status=True)
        q2 = q1.order_by('roll_number')
        return q2


class StudentListForTest(generics.ListCreateAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        test_id = self.kwargs['test_id']

        query_set = ClassTest.objects.filter(pk=test_id)[:1]
        for q in query_set:
            the_class = q.the_class
            print ('class=')
            print (the_class)

            section = q.section
            print ('section=')
            print (section)

        q1 = Student.objects.filter(current_section__section=section,
                                    current_class__standard=the_class, active_status=True)
        q2 = q1.order_by('roll_number')
        return q2


class StudentListForParent(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        parent_mobile = self.kwargs['parent_mobile']

        the_parent = Parent.objects.get(parent_mobile1=parent_mobile)
        q1 = Student.objects.filter(parent=the_parent).order_by('fist_name')
        return q1


def get_parent(request, student_id):
    parent_detail = {

    }

    if request.method == 'GET':
        try:
            student = Student.objects.get(id=student_id)
            parent = student.parent
            parent_detail['parent_name'] = parent.parent_name
            parent_detail['parent_mobile1'] = parent.parent_mobile1
            parent_detail['parent_mobile2'] = parent.parent_mobile2
            parent_detail['status'] = 'ok'
        except Exception as e:
            print ('Exception1 from student views.py = %s (%s)' % (e.message, type(e)))
            print('unable to fetch parent name and mobile for student id: ' + student_id)
            parent_detail['status'] = 'error'
            return JSONResponse(parent_detail, status=201)

        return JSONResponse(parent_detail, status=201)


class ParentList(generics.ListAPIView):
    serializer_class = ParentSerializer

    def get_queryset(self):
        print('inside queryset')
        student_id = self.kwargs['student_id']

        q = Parent.objects.filter(student__id=student_id)
        return q

