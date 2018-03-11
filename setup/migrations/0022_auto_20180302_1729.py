# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0021_globalconf_aws_region'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='configurations',
            options={'ordering': ('school__school_name',)},
        ),
    ]
