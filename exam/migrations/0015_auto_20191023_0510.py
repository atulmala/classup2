# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0014_wing'),
    ]

    operations = [
        migrations.AddField(
            model_name='marksheet',
            name='logo_left_margin',
            field=models.IntegerField(default=410),
        ),
        migrations.AddField(
            model_name='marksheet',
            name='logo_width',
            field=models.IntegerField(default=65),
        ),
    ]
