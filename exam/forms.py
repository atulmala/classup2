from django import forms

from setup.models import School
from academics.models import Class, Section


class TermResultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        from django.forms.widgets import HiddenInput
        school_id = kwargs.pop('school_id')

        super(TermResultForm, self).__init__(*args, **kwargs)
        school = School.objects.get(id=school_id)
        self.fields['the_class'] = forms.ModelChoiceField(queryset=Class.objects.filter(school=school).
                                                          order_by('sequence'), label='Class',
                                                          widget=forms.Select(attrs={'onchange' :'get_students();'}))
        self.fields['the_class'].empty_label = None
        self.fields['section'] = forms.ModelChoiceField(queryset=Section.objects.filter(school=school).
                                                        order_by('section'), label='Section',
                                                        widget=forms.Select(attrs={'onchange' :'get_students();'}))
        self.fields['section'].empty_label = None

        SELECT_STUDENT_CHOICES = ('All Students', 'Selected Students')

        self.fields['select_students'] = forms.ChoiceField(required=False,
                                                           widget=forms.CheckboxInput,
                                                           choices=SELECT_STUDENT_CHOICES)
        self.fields['students'] = forms.ChoiceField()

        self.fields['school_id'] = forms.CharField(initial=school_id)

        self.fields['school_id'].widget = HiddenInput()


class ResultSheetForm(forms.Form):
    def __init__(self, *args, **kwargs):
        school_id = kwargs.pop('school_id')
        super(ResultSheetForm, self).__init__(*args, **kwargs)
        school = School.objects.get(id=school_id)
        self.fields['the_class'] = forms.ModelChoiceField(queryset=Class.objects.filter(school=school).
                                                          order_by('sequence'), label='Class')
        self.fields['section'] = forms.ModelChoiceField(queryset=Section.objects.filter(school=school).
                                                        order_by('section'), label='Section')