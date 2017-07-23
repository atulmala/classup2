# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0010_log_book'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log_book',
            name='school',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='log_book',
            name='user',
            field=models.CharField(max_length=100),
        ),
    ]
