# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='loginrecord',
            name='string_ip',
            field=models.CharField(default='dummy', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='loginrecord',
            name='ip_address',
            field=models.GenericIPAddressField(null=True),
        ),
    ]
