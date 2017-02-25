# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0003_teacher_active_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='teacher_erp_id',
            field=models.CharField(max_length=30),
        ),
    ]
