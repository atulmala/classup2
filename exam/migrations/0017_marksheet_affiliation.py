# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0016_scheme_max_marks'),
    ]

    operations = [
        migrations.AddField(
            model_name='marksheet',
            name='affiliation',
            field=models.CharField(default=b'Affiliated to CBSE', max_length=200),
        ),
    ]
