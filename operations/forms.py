__author__ = 'atulgupta'

from django import forms
from functools import partial

from academics.models import Class, Section, Subject

DateInput = partial(forms.DateInput, {'class': 'datepicker'})
MonthInput = partial(forms.DateInput, {'class': 'monthpicker'})


class SchoolAttSummaryForm(forms.Form):
    date = forms.DateField(widget=DateInput())


class AttendanceRegisterForm(forms.Form):
    date = forms.CharField(widget=MonthInput(), label='Select Month & Year')
    the_class = forms.ModelChoiceField(queryset=Class.objects.all().order_by('sequence'), label='Class')
    section = forms.ModelChoiceField(queryset=Section.objects.all().order_by('section'), label='Section')
    subject = forms.ModelChoiceField(queryset=Subject.objects.all().order_by('subject_sequence'), label='Subject')


class TestResultForm(forms.Form):
    start_date = forms.DateField(widget=DateInput())
    end_date = forms.DateField(widget=DateInput())
    the_class = forms.ModelChoiceField(queryset=Class.objects.all().order_by('sequence'), label='Class')
    section = forms.ModelChoiceField(queryset=Section.objects.all().order_by('section'), label='Section')
    term = forms.CharField(label='Please enter a Term for this test (ex Term I, Term II...')


class ParentsCommunicationDetailsForm(forms.Form):
    date = forms.CharField(widget=MonthInput(), label='Select Month & Year')