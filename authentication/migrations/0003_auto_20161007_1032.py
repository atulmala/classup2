# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_auto_20161007_0423'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='loginrecord',
            name='city',
        ),
        migrations.RemoveField(
            model_name='loginrecord',
            name='country',
        ),
        migrations.RemoveField(
            model_name='loginrecord',
            name='result',
        ),
    ]
