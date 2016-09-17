# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(default=datetime.datetime.now)),
                ('message', models.TextField()),
                ('recipient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(to='teacher.Teacher')),
            ],
        ),
    ]
