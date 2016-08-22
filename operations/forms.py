__author__ = 'atulgupta'

from django import forms

from functools import partial

from setup.models import School
from academics.models import Class, Section, Subject

DateInput = partial(forms.DateInput, {'class': 'datepicker'})
MonthInput = partial(forms.DateInput, {'class': 'monthpicker'})


class SchoolAttSummaryForm(forms.Form):
    date = forms.DateField(widget=DateInput())


class AttendanceRegisterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        school_id = kwargs.pop('school_id')
        super(AttendanceRegisterForm, self).__init__(*args, **kwargs)
        school = School.objects.get(id=school_id)
        self.fields['the_class'] = forms.ModelChoiceField(queryset=Class.objects.filter(school=school).
                                                          order_by('sequence'), label='Class')
        self.fields['section'] = forms.ModelChoiceField(queryset=Section.objects.filter(school=school).
                                                        order_by('section'), label='Section')
        self.fields['subject'] = forms.ModelChoiceField(queryset=Subject.objects.filter(school=school).
                                                        order_by('subject_sequence'), label='Subject')
    date = forms.CharField(widget=MonthInput(), label='Select Month & Year')


class TestResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        school_id = kwargs.pop('school_id')
        super(TestResultForm, self).__init__(*args, **kwargs)
        school = School.objects.get(id=school_id)
        self.fields['the_class'] = forms.ModelChoiceField(queryset=Class.objects.filter(school=school).
                                                          order_by('sequence'), label='Class')
        self.fields['section'] = forms.ModelChoiceField(queryset=Section.objects.filter(school=school).
                                                        order_by('section'), label='Section')
    start_date = forms.DateField(widget=DateInput())
    end_date = forms.DateField(widget=DateInput())
    term = forms.CharField(label='Please enter a Term for this test (ex Term I, Term II...')


class ParentsCommunicationDetailsForm(forms.Form):
    date = forms.CharField(widget=MonthInput(), label='Select Month & Year')