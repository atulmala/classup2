# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0020_marksheet_affiliation_start'),
    ]

    operations = [
        migrations.AddField(
            model_name='marksheet',
            name='two_page',
            field=models.BooleanField(default=False),
        ),
    ]
