__author__ = 'atulmala'

from django import forms

class ExcelFileUploadForm(forms.Form):
    error = forms.Textarea
    excelFile = forms.FileField(label='Select the Excel/CSV File', help_text='max 1 MB')


