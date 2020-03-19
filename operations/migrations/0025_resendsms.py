# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0024_smsrecord_sms_consumed'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResendSMS',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('outcome', models.TextField(default=b'Not Available', max_length=30)),
                ('status', models.CharField(default=b'Not Available', max_length=350)),
                ('sms_record', models.ForeignKey(to='operations.SMSRecord')),
            ],
        ),
    ]
