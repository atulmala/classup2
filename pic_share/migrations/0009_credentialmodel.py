# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oauth2client.contrib.django_util.models


class Migration(migrations.Migration):

    dependencies = [
        ('pic_share', '0008_sharedwithteacher'),
    ]

    operations = [
        migrations.CreateModel(
            name='CredentialModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('credential', oauth2client.contrib.django_util.models.CredentialsField(null=True)),
            ],
        ),
    ]
