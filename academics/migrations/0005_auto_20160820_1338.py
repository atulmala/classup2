# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0004_auto_20160819_1245'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teachersubjects',
            name='school',
        ),
        migrations.RemoveField(
            model_name='testresults',
            name='school',
        ),
    ]
