# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Configurations',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('router_server_ip', models.CharField(max_length=50)),
                ('school_group_id', models.CharField(default=None, max_length=10)),
                ('send_absence_sms', models.BooleanField(default=True)),
                ('send_period_bunk_sms', models.BooleanField(default=False)),
                ('send_marks_sms', models.BooleanField(default=True)),
                ('send_results_sms', models.BooleanField(default=True)),
                ('send_test_scheduled_sms', models.BooleanField(default=False)),
                ('send_bus_reached_to_school_sms', models.BooleanField(default=False)),
                ('send_bus_started_from_school_sms', models.BooleanField(default=False)),
                ('send_all_parent_sms_to_principal', models.BooleanField(default=False)),
                ('session_start_month', models.IntegerField(default=4)),
                ('principal_mobile', models.CharField(default=b'1234567890', max_length=20)),
                ('admin1_mobile', models.CharField(default=b'1234567890', max_length=20)),
                ('admin2_mobile', models.CharField(default=b'1234567890', max_length=20)),
                ('admin3_mobile', models.CharField(default=b'1234567890', max_length=20)),
                ('admin4_mobile', models.CharField(default=b'1234567890', max_length=20)),
                ('transport_incharge_mobile', models.CharField(default=b'1234567890', max_length=20)),
                ('absence_sms_prolog', models.CharField(default=None, max_length=200, null=True)),
                ('absence_sms_epilog', models.CharField(default=None, max_length=200, null=True)),
                ('marks_sms_prolog', models.CharField(default=None, max_length=200, null=True)),
                ('marks_sms_epilog', models.CharField(default=None, max_length=200, null=True)),
                ('results_sms_prolog', models.CharField(default=None, max_length=200, null=True)),
                ('results_sms_epilog', models.CharField(default=None, max_length=200, null=True)),
                ('bunk_sms_prolog', models.CharField(default=None, max_length=200, null=True)),
                ('bunk_sms_epilog', models.CharField(default=None, max_length=200, null=True)),
                ('teacher_sms_prolog', models.CharField(default=None, max_length=200, null=True)),
                ('teacher_sms_epilog', models.CharField(default=None, max_length=200, null=True)),
                ('google_play_link', models.CharField(default=None, max_length=100, null=True)),
                ('app_store_link', models.CharField(default=None, max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('school_id', models.CharField(unique=True, max_length=10)),
                ('school_name', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='configurations',
            name='school',
            field=models.ForeignKey(to='setup.School'),
        ),
    ]
