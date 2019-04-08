# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0023_auto_20180830_1504'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userschoolmapping',
            options={'ordering': ['user']},
        ),
    ]
