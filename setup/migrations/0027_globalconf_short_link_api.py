# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0026_configurations_include_welcome_sms'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalconf',
            name='short_link_api',
            field=models.CharField(default=b'4f79464452b3bbed98ae6b42d717ac399cbaa', max_length=100),
        ),
    ]
