# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pic_share', '0004_imagevideo_active_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagevideo',
            name='short_link',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
