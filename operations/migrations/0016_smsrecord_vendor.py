# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0015_classupadmin'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='vendor',
            field=models.CharField(default=b'1', max_length=3),
        ),
    ]
