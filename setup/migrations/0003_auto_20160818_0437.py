# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0002_auto_20160818_0437'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configurations',
            name='router_server_ip',
            field=models.CharField(default=b'0.0.0.0', max_length=50),
        ),
    ]
