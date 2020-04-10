# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0026_smsbatch'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='push_outcome',
            field=models.TextField(default=b'Not Attempted', max_length=50),
        ),
    ]
