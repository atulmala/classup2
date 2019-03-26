# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_auto_20180329_1858'),
        ('setup', '0023_auto_20180830_1504'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectAdmFee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('school', models.ForeignKey(to='setup.School')),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
