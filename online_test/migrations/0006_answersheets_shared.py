# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('online_test', '0005_answersheets'),
    ]

    operations = [
        migrations.AddField(
            model_name='answersheets',
            name='shared',
            field=models.BooleanField(default=False),
        ),
    ]
