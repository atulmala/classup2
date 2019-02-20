# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0028_auto_20190220_1418'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subject',
            name='theory_marks',
            field=models.DecimalField(default=70.0, max_digits=6, decimal_places=2),
        ),
    ]
