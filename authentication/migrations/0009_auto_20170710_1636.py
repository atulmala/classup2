# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0008_auto_20170313_0924'),
    ]

    operations = [
        migrations.AddField(
            model_name='loginrecord',
            name='model',
            field=models.CharField(default=b'Not available', max_length=200),
        ),
        migrations.AddField(
            model_name='loginrecord',
            name='os',
            field=models.CharField(default=b'Not available', max_length=200),
        ),
        migrations.AddField(
            model_name='loginrecord',
            name='resolution',
            field=models.CharField(default=b'Not available', max_length=100),
        ),
        migrations.AddField(
            model_name='loginrecord',
            name='size',
            field=models.CharField(default=b'Not available', max_length=100),
        ),
    ]
