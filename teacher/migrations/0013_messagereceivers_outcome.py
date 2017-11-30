# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0012_messagereceivers_status_extracted'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagereceivers',
            name='outcome',
            field=models.TextField(default=b'Awaited', max_length=20),
        ),
    ]
