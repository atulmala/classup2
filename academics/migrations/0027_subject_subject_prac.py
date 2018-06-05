# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0026_auto_20180514_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='subject_prac',
            field=models.BooleanField(default=False),
        ),
    ]
