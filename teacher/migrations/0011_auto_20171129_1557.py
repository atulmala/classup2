# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_dob'),
        ('teacher', '0010_auto_20171109_1116'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageReceivers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_message', models.TextField()),
                ('status', models.CharField(max_length=100, null=True)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
        migrations.CreateModel(
            name='TeacherMessageRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
                ('message', models.TextField()),
                ('sent_to', models.CharField(max_length=20)),
                ('the_class', models.CharField(max_length=30, null=True)),
                ('section', models.CharField(max_length=30, null=True)),
                ('activity_group', models.CharField(max_length=50, null=True)),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
            ],
        ),
        migrations.AddField(
            model_name='messagereceivers',
            name='teacher_record',
            field=models.ForeignKey(to='teacher.TeacherMessageRecord'),
        ),
    ]
