# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0019_auto_20171031_2142'),
        ('teacher', '0010_auto_20171109_1116'),
        ('time_table', '0003_excludedfromarrangements'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExcludedFromArrangements1',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('school', models.ForeignKey(to='setup.School')),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
            ],
        ),
    ]
