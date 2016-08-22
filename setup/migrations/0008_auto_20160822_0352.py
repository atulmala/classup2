# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0007_configurations_enable_bus_attendance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configurations',
            name='app_store_link',
            field=models.CharField(default=b'http://onelink.to/ajfj3j', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='google_play_link',
            field=models.CharField(default=b'https://play.google.com/store/apps/details?id=com.classup', max_length=100, null=True),
        ),
    ]
