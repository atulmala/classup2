# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0017_configurations_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('authentication', '0009_auto_20170710_1636'),
    ]

    operations = [
        migrations.CreateModel(
            name='log_book',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_and_time', models.DateTimeField(default=datetime.datetime.now)),
                ('user_name', models.CharField(max_length=100)),
                ('event', models.CharField(max_length=200)),
                ('category', models.CharField(max_length=20)),
                ('outcome', models.BooleanField()),
                ('school', models.ForeignKey(to='setup.School')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
