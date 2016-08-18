
# Create your views here.

from rest_framework import generics

from .models import Student, Parent
from academics.models import Class, Section, ClassTest

from .serializers import StudentSerializer


class StudentList(generics.ListAPIView):
    serializer_class = StudentSerializer

    def get_queryset(self):
        """
        :return: list of all students based on class and section supplied by the URL
        """
        print self.request._request
        print self.kwargs

        the_class = self.kwargs['the_class']
        section = self.kwargs['section']

        q1 = Student.objects.filter(current_section__section=section,
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
            print 'class='
            print the_class

            section = q.section
            print 'section='
            print section

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

