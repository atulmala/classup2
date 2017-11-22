# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0019_auto_20171031_2142'),
        ('teacher', '0010_auto_20171109_1116'),
        ('academics', '0020_subject_subject_type'),
        ('time_table', '0004_excludedfromarrangements1'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassWingMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('school', models.ForeignKey(to='setup.School')),
                ('the_class', models.ForeignKey(to='academics.Class')),
                ('wing', models.ForeignKey(to='time_table.Wing')),
            ],
        ),
        migrations.CreateModel(
            name='TeacherWingMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('school', models.ForeignKey(to='setup.School')),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
                ('wing', models.ForeignKey(to='time_table.Wing')),
            ],
        ),
    ]
