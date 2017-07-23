# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0017_configurations_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalConf',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('server_url', models.CharField(default=b'https://www.classupclient.com/', max_length=100)),
            ],
        ),
    ]
