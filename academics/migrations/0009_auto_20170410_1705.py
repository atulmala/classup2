# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0008_auto_20170409_2333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hw',
            name='notes',
            field=models.CharField(default=b'No comments', max_length=200),
        ),
    ]
