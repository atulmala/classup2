# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('online_test', '0006_answersheets_shared'),
    ]

    operations = [
        migrations.AddField(
            model_name='studenttestattempt',
            name='submission_ok',
            field=models.BooleanField(default=True),
        ),
    ]
