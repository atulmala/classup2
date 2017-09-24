# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_auto_20160917_0912'),
    ]

    operations = [
        migrations.CreateModel(
            name='DOB',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dob', models.DateField()),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
