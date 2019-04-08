# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0024_auto_20190408_1129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configurations',
            name='app_store_link',
            field=models.CharField(default=b'https://itunes.apple.com/us/app/classup/id1100776259?mt=8&uo=4', max_length=100, null=True),
        ),
    ]
