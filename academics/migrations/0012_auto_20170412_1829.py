# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0011_auto_20170412_1821'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hw',
            name='location',
            field=models.ImageField(upload_to=b'homework/'),
        ),
    ]
