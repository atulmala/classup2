# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0020_subject_subject_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='termtestresult',
            name='prac_marks',
            field=models.DecimalField(null=True, max_digits=6, decimal_places=2),
        ),
    ]
