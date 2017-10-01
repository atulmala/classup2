# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0017_auto_20170929_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coscholastics',
            name='art_education',
            field=models.CharField(default=b' ', max_length=4, blank=True),
        ),
        migrations.AlterField(
            model_name='coscholastics',
            name='discipline',
            field=models.CharField(default=b' ', max_length=4, blank=True),
        ),
        migrations.AlterField(
            model_name='coscholastics',
            name='health_education',
            field=models.CharField(default=b' ', max_length=4, blank=True),
        ),
        migrations.AlterField(
            model_name='coscholastics',
            name='promoted_to_class',
            field=models.CharField(default=b' ', max_length=10, blank=b'True'),
        ),
        migrations.AlterField(
            model_name='coscholastics',
            name='work_education',
            field=models.CharField(default=b' ', max_length=4, blank=True),
        ),
    ]
