# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0013_additionaldetails_date_of_admission'),
        ('teacher', '0018_auto_20190909_1630'),
        ('academics', '0031_subject_grade_based'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnlineQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.CharField(max_length=400)),
                ('option_a', models.CharField(max_length=200)),
                ('option_b', models.CharField(max_length=200)),
                ('option_c', models.CharField(max_length=200)),
                ('option_d', models.CharField(max_length=200)),
                ('correct_option', models.CharField(max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='OnlineTest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('duration', models.IntegerField(default=30)),
                ('subject', models.ForeignKey(to='academics.Subject')),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
        migrations.CreateModel(
            name='StudentQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer_marked', models.CharField(max_length=5)),
                ('whether_correct', models.BooleanField(default=False)),
                ('question', models.ForeignKey(to='online_test.OnlineQuestion')),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
        migrations.AddField(
            model_name='onlinequestion',
            name='test',
            field=models.ForeignKey(to='online_test.OnlineTest'),
        ),
    ]
