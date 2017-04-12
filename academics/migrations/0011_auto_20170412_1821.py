# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0010_hw_school'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homework',
            name='location',
            field=models.ImageField(upload_to=b'homework/'),
        ),
    ]
