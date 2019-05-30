# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_auto_20180329_1858'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='parent',
            options={'ordering': ('parent_name',)},
        ),
    ]
