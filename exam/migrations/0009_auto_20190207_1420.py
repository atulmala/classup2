# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0008_marksheet'),
    ]

    operations = [
        migrations.AddField(
            model_name='marksheet',
            name='place',
            field=models.CharField(default=b'Place', max_length=150),
        ),
        migrations.AddField(
            model_name='marksheet',
            name='result_date',
            field=models.CharField(default=b'20/03/2019', max_length=10),
        ),
    ]
