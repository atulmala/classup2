# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0027_subject_subject_prac'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='prac_marks',
            field=models.DecimalField(default=30.0, max_digits=6, decimal_places=2),
        ),
        migrations.AddField(
            model_name='subject',
            name='theory_marks',
            field=models.DecimalField(default=80.0, max_digits=6, decimal_places=2),
        ),
    ]
