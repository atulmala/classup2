# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0010_configurations_send_absence_sms_both_to_parent'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_name', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='school',
            name='group',
            field=models.ForeignKey(to='setup.SchoolGroup', null=True),
        ),
    ]
