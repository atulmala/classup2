# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0025_auto_20180513_2148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classtest',
            name='exam',
            field=models.ForeignKey(to='academics.Exam', null=True),
        ),
    ]
