# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activity_groups', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitymembers',
            name='group',
            field=models.ForeignKey(to='activity_groups.ActivityGroup', null=True),
        ),
    ]
