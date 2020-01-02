# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0019_examresult'),
    ]

    operations = [
        migrations.AddField(
            model_name='marksheet',
            name='affiliation_start',
            field=models.IntegerField(default=180),
        ),
    ]
