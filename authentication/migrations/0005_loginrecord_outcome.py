# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_loginrecord_login_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='loginrecord',
            name='outcome',
            field=models.CharField(default=b'Failed', max_length=10),
        ),
    ]
