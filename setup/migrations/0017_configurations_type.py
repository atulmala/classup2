# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0016_configurations_login_prefix'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='type',
            field=models.CharField(default=b'school', max_length=20),
        ),
    ]
