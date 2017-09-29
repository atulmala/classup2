# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_dob'),
        ('academics', '0015_auto_20170923_2325'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoScholastics',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=10)),
                ('work_education', models.CharField(default=b' ', max_length=4)),
                ('art_education', models.CharField(default=b' ', max_length=4)),
                ('health_education', models.CharField(default=b' ', max_length=4)),
                ('discipline', models.CharField(default=b' ', max_length=4)),
                ('teacher_remarks', models.CharField(max_length=100, null=True, blank=True)),
                ('promoted_to_class', models.CharField(max_length=10, null=True, blank=True)),
                ('section', models.ForeignKey(to='academics.Section', null=True)),
                ('student', models.ForeignKey(to='student.Student')),
                ('the_class', models.ForeignKey(to='academics.Class', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('grade', models.CharField(max_length=4)),
            ],
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(default=b'Term 1', max_length=10)),
            ],
        ),
    ]
