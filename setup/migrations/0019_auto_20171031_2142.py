# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0018_globalconf'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='school',
            options={'ordering': ['school_name']},
        ),
    ]
