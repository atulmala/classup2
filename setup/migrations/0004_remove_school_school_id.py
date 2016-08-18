# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0003_auto_20160818_0437'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='school',
            name='school_id',
        ),
    ]
