# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0017_auto_20190702_1648'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSVendor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('vendor', models.CharField(default=b'SoftSMS', max_length=25)),
            ],
        ),
    ]
