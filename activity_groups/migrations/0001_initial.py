# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0019_auto_20171031_2142'),
        ('student', '0004_dob'),
        ('teacher', '0010_auto_20171109_1116'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_name', models.CharField(max_length=100)),
                ('group_description', models.CharField(default=b'Activity Group', max_length=100)),
                ('group_incharge', models.ForeignKey(to='teacher.Teacher')),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
        migrations.CreateModel(
            name='ActivityMembers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
