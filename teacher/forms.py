from django import forms
from django.forms.widgets import HiddenInput

from setup.models import School
from .models import Teacher


class TeacherAttendanceForm (forms.ModelForm):
    def __init__(self, *args, **kwargs):
        school_id = kwargs.pop('school_id')

        super(TeacherAttendanceForm, self).__init__(*args, **kwargs)
        school = School.objects.get(id=school_id)
        self.fields['teachers'] = forms.ModelChoiceField(queryset=Teacher.objects.filter(school=school).
                                                         order_by('first_name'), label='Teacher List')
        self.fields['school_id'] = forms.CharField(initial=school_id)

        self.fields['school_id'].widget = HiddenInput()