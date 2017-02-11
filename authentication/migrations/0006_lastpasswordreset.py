# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0005_loginrecord_outcome'),
    ]

    operations = [
        migrations.CreateModel(
            name='LastPasswordReset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('login_id', models.CharField(max_length=100)),
                ('last_reset_time', models.DateTimeField()),
            ],
        ),
    ]
