# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0003_auto_20160817_1644'),
    ]

    operations = [
        migrations.AlterField(
            model_name='class',
            name='standard',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='section',
            name='section',
            field=models.CharField(max_length=5),
        ),
        migrations.AlterField(
            model_name='subject',
            name='subject_code',
            field=models.CharField(max_length=10),
        ),
    ]
