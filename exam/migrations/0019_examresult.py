# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0012_auto_20191117_0304'),
        ('exam', '0018_marksheet_board_logo_path'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.BooleanField(default=True)),
                ('detain_reason', models.CharField(default=b'N/A', max_length=200)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
