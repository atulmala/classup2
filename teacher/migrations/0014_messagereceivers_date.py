# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0013_messagereceivers_outcome'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagereceivers',
            name='date',
            field=models.DateTimeField(null=True),
        ),
    ]
