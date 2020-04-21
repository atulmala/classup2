# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0013_additionaldetails_date_of_admission'),
        ('online_test', '0003_onlinetest_exam'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentTestAttempt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('online_test', models.ForeignKey(to='online_test.OnlineTest')),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
