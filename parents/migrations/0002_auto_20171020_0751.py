# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parentcommunication',
            name='communication_text',
            field=models.CharField(max_length=400),
        ),
    ]
