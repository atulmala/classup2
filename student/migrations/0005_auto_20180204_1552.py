# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_dob'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='student',
            options={'ordering': ('fist_name',)},
        ),
    ]
