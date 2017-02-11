# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0014_smsrecord_sender_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassUpAdmin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('admin_mobile', models.CharField(default=b'9873011186', max_length=20)),
            ],
        ),
    ]
