# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0009_school_subscription_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='configurations',
            name='send_absence_sms_both_to_parent',
            field=models.BooleanField(default=True),
        ),
    ]
