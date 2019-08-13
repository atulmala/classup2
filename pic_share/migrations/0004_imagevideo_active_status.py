# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pic_share', '0003_sharewithstudents'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagevideo',
            name='active_status',
            field=models.BooleanField(default=True),
        ),
    ]
