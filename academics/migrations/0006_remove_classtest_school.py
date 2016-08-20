# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0005_auto_20160820_1338'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classtest',
            name='school',
        ),
    ]
