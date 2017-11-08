# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0019_thirdlang'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='subject_type',
            field=models.CharField(default=b'Regular', max_length=40),
        ),
    ]
