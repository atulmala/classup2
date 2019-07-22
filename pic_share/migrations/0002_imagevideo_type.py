# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pic_share', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagevideo',
            name='type',
            field=models.CharField(default=b'image', max_length=10),
        ),
    ]
