# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0017_marksheet_affiliation'),
    ]

    operations = [
        migrations.AddField(
            model_name='marksheet',
            name='board_logo_path',
            field=models.CharField(default=b'classup2/media/dev/cbse_logo/Logo/cbse-logo.png', max_length=100),
        ),
    ]
