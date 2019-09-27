# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0027_globalconf_short_link_api'),
        ('exam', '0013_stream_streammapping'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wing', models.CharField(max_length=50)),
                ('classes', models.CharField(max_length=100)),
                ('school', models.ForeignKey(related_name='school', to='setup.School')),
            ],
        ),
    ]
