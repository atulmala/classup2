# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0008_additionaldetails_gender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='roll_number',
            field=models.IntegerField(default=50),
        ),
    ]
