# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0004_remove_school_school_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='school_address',
            field=models.CharField(max_length=200, blank=True),
        ),
    ]
