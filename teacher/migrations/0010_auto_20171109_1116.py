# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0019_auto_20171031_2142'),
        ('teacher', '0009_teacherattendncetaken'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacherattendance',
            name='school',
            field=models.ForeignKey(to='setup.School', null=True),
        ),
        migrations.AddField(
            model_name='teacherattendncetaken',
            name='school',
            field=models.ForeignKey(to='setup.School', null=True),
        ),
    ]
