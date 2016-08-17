# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0001_initial'),
        ('academics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('parent_name', models.CharField(max_length=100)),
                ('parent_mobile1', models.CharField(max_length=20)),
                ('parent_mobile2', models.CharField(max_length=20, null=True, blank=True)),
                ('parent_email', models.EmailField(max_length=254, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('student_erp_id', models.CharField(max_length=20, unique=True, null=True, db_column=b'student_erp_id', blank=True)),
                ('fist_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('roll_number', models.IntegerField()),
                ('active_status', models.BooleanField(default=True)),
                ('current_class', models.ForeignKey(to='academics.Class')),
                ('current_section', models.ForeignKey(to='academics.Section')),
                ('parent', models.ForeignKey(default=None, to='student.Parent')),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
