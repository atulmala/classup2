# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0005_auto_20180204_1552'),
        ('exam', '0005_notpromoted'),
    ]

    operations = [
        migrations.CreateModel(
            name='NPromoted',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
