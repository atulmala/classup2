# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('online_test', '0007_studenttestattempt_submission_ok'),
    ]

    operations = [
        migrations.AddField(
            model_name='studenttestattempt',
            name='submitted_via',
            field=models.CharField(default=b'smpartphone', max_length=15),
        ),
    ]
