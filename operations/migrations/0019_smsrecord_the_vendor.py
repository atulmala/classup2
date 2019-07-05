# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0018_smsvendor'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsrecord',
            name='the_vendor',
            field=models.ForeignKey(blank=True, to='operations.SMSVendor', null=True),
        ),
    ]
