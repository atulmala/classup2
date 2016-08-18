# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParentCommunication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_sent', models.DateField()),
                ('communication_text', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ParentCommunicationCategories',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='parentcommunication',
            name='category',
            field=models.ForeignKey(to='parents.ParentCommunicationCategories'),
        ),
        migrations.AddField(
            model_name='parentcommunication',
            name='student',
            field=models.ForeignKey(to='student.Student'),
        ),
    ]
