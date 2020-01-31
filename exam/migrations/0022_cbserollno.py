# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0012_auto_20191117_0304'),
        ('exam', '0021_marksheet_two_page'),
    ]

    operations = [
        migrations.CreateModel(
            name='CBSERollNo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cbse_roll_no', models.CharField(max_length=10)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
