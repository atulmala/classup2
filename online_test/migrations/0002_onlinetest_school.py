# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0027_globalconf_short_link_api'),
        ('online_test', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='onlinetest',
            name='school',
            field=models.ForeignKey(to='setup.School', null=True),
        ),
    ]
