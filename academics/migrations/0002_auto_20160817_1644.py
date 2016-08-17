# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
        ('setup', '0001_initial'),
        ('academics', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='testresults',
            name='student',
            field=models.ForeignKey(to='student.Student', db_column=b'student_erp_id'),
        ),
        migrations.AddField(
            model_name='teachersubjects',
            name='school',
            field=models.ForeignKey(to='setup.School'),
        ),
        migrations.AddField(
            model_name='teachersubjects',
            name='subject',
            field=models.ForeignKey(to='academics.Subject'),
        ),
    ]
