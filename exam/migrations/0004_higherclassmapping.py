# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_dob'),
        ('academics', '0020_subject_subject_type'),
        ('exam', '0003_scheme_subject_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='HigherClassMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('student', models.ForeignKey(to='student.Student')),
                ('subject', models.ForeignKey(to='academics.Subject')),
            ],
        ),
    ]
