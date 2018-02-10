# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0019_auto_20171031_2142'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='school_short_name',
            field=models.CharField(default=b'model', max_length=20),
        ),
        migrations.AddField(
            model_name='globalconf',
            name='aws_access_key',
            field=models.CharField(default=b'AKIAJ6X32EHNR26CXSWA', max_length=40),
        ),
        migrations.AddField(
            model_name='globalconf',
            name='aws_s3_bucket',
            field=models.CharField(default=b'classup2', max_length=20),
        ),
        migrations.AddField(
            model_name='globalconf',
            name='aws_secret_key',
            field=models.CharField(default=b'955aB0s0zK0iuE5NZUevaYOx2SGe6e7EUNvB89Zg', max_length=50),
        ),
    ]
