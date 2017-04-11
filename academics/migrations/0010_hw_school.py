# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0016_configurations_login_prefix'),
        ('academics', '0009_auto_20170410_1705'),
    ]

    operations = [
        migrations.AddField(
            model_name='hw',
            name='school',
            field=models.ForeignKey(to='setup.School', null=True),
        ),
    ]
