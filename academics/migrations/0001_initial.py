# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('standard', models.CharField(unique=True, max_length=20)),
                ('sequence', models.SmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ClassTeacher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='ClassTest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_conducted', models.DateField()),
                ('max_marks', models.DecimalField(max_digits=6, decimal_places=2)),
                ('passing_marks', models.DecimalField(max_digits=6, decimal_places=2)),
                ('grade_based', models.BooleanField()),
                ('is_completed', models.BooleanField(default=False)),
                ('test_type', models.CharField(default=b'Terminal', max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('start_class', models.CharField(max_length=20, null=True)),
                ('start_class_sequence', models.SmallIntegerField(null=True)),
                ('end_class', models.CharField(max_length=20, null=True)),
                ('end_class_sequence', models.SmallIntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('section', models.CharField(unique=True, max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject_name', models.CharField(max_length=40)),
                ('subject_code', models.CharField(unique=True, max_length=10)),
                ('subject_sequence', models.SmallIntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TeacherSubjects',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='TestResults',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('roll_no', models.IntegerField(null=True)),
                ('marks_obtained', models.DecimalField(null=True, max_digits=6, decimal_places=2)),
                ('grade', models.CharField(max_length=15, null=True)),
                ('class_test', models.ForeignKey(to='academics.ClassTest')),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
        migrations.CreateModel(
            name='WorkingDays',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year', models.SmallIntegerField()),
                ('month', models.SmallIntegerField()),
                ('working_days', models.SmallIntegerField()),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
