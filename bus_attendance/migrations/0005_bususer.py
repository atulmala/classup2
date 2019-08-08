# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0011_auto_20190530_1657'),
        ('bus_attendance', '0004_busfeeslab_school'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
