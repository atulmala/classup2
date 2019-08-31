# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0027_globalconf_short_link_api'),
        ('maintenance', '0002_auto_20190722_0803'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyMessageCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('message_count', models.IntegerField()),
                ('sms_count', models.IntegerField()),
                ('school', models.ForeignKey(to='setup.School')),
            ],
        ),
    ]
