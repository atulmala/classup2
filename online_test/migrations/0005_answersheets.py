# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0013_additionaldetails_date_of_admission'),
        ('online_test', '0004_studenttestattempt'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnswerSheets',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('link', models.CharField(max_length=200)),
                ('online_test', models.ForeignKey(to='online_test.OnlineTest')),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
