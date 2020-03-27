# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0018_auto_20190909_1630'),
        ('academics', '0031_subject_grade_based'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lecture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('topic', models.CharField(max_length=100)),
                ('youtube_link', models.CharField(max_length=200, null=True)),
                ('pdf_link', models.CharField(max_length=200, null=True)),
                ('section', models.ForeignKey(to='academics.Section', null=True)),
                ('subject', models.ForeignKey(to='academics.Subject')),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
    ]
