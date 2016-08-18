# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configurations',
            name='absence_sms_epilog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='absence_sms_prolog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='app_store_link',
            field=models.CharField(default=b' ', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='bunk_sms_epilog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='bunk_sms_prolog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='google_play_link',
            field=models.CharField(default=b' ', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='marks_sms_epilog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='marks_sms_prolog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='results_sms_epilog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='results_sms_prolog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='teacher_sms_epilog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='configurations',
            name='teacher_sms_prolog',
            field=models.CharField(default=b' ', max_length=200, null=True),
        ),
    ]
