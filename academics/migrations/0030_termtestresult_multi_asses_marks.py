# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0029_auto_20190220_1423'),
    ]

    operations = [
        migrations.AddField(
            model_name='termtestresult',
            name='multi_asses_marks',
            field=models.DecimalField(default=0.0, null=True, max_digits=6, decimal_places=2),
        ),
    ]
