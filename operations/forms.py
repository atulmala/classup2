from django import forms

from functools import partial
from django.utils.safestring import mark_safe

from setup.models import School
from academics.models import Class, Section, Subject

__author__ = 'atulgupta'

DateInput = partial(forms.DateInput, {'class': 'datepicker'})
MonthInput = partial(forms.DateInput, {'class': 'monthpicker'})

STAFF_CHOICES = (
    ('teacher', 'Teachers'),
)


class HorizontalRenderer(forms.CheckboxSelectMultiple.renderer):
    def render(self):
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))


class SchoolAttSummaryForm(forms.Form):
    date = forms.DateField(widget=DateInput(), label='Date(mm/dd/yyyy) ')


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


class BulkSMSForm(forms.Form):
    def __init__(self, *args, **kwargs):
        school_id = kwargs.pop('school_id')
        super(BulkSMSForm, self).__init__(*args, **kwargs)
        school = School.objects.get(id=school_id)
        self.fields['Class'] = forms.ModelChoiceField(queryset=Class.objects.filter(school=school).
                                                      order_by('sequence'), to_field_name='standard',
                                                      label='Select Class', widget=forms.CheckboxSelectMultiple
                                                      (renderer=HorizontalRenderer))
        self.fields['Class'].empty_label = None

    message_text = forms.CharField(widget=forms.Textarea, label='Enter Message')
    Staff = forms.MultipleChoiceField(choices=STAFF_CHOICES,
                                      widget=forms.CheckboxSelectMultiple(renderer=HorizontalRenderer))
