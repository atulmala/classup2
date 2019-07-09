from django.db.models import Count, Max
from django.http import HttpResponse
from rest_framework.renderers import JSONRenderer
from rest_framework import generics

from attendance.models import Attendance


class JSONResponse(HttpResponse):
    """
    an HttpResponse that renders its contents to JSON
    """

    def __init__(self, data, **kwargs):
        print ('from JSONResponse...')
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


class DeDup(generics.ListCreateAPIView):
    def post(self, request, *args, **kwargs):
        context_dict = {

        }
        unique_fields = ['date', 'the_class', 'section', 'subject', 'student', 'taken_by']
        print('try to identify duplicate entries')
        try:
            duplicates = (
                Attendance.objects.values(*unique_fields)
                    .order_by()
                    .annotate(max_id=Max('id'), count_id=Count('id'))
                    .filter(count_id__gt=1)
            )

            for duplicate in duplicates:
                print(duplicate)
                (
                    Attendance.objects
                        .filter(**{x: duplicate[x] for x in unique_fields})
                        .exclude(id=duplicate['max_id'])
                        .delete()
                )
            context_dict['outcome'] = 'success'
            return JSONResponse(context_dict, status=200)
        except Exception as e:
            print('exception 09072019-A from maintenance views.py %s %s' % (e.message, type(e)))
            print('failed in removing duplicate records from Attendance Table')
            context_dict['outcome'] = 'failed'
            return JSONResponse

