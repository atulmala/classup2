# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0030_termtestresult_multi_asses_marks'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='grade_based',
            field=models.BooleanField(default=False),
        ),
    ]
