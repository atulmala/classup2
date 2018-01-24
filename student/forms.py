from django import forms

from setup.models import School


class MidTermAdmissionForm (forms.Form):
    def __init__(self, *args, **kwargs):
        school_id = kwargs.pop('school_id')
        super(MidTermAdmissionForm, self).__init__(*args, **kwargs)
        school = School.objects.get(id=school_id)
    admission_no = forms.CharField(label='Admission/Reg. No.')