# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0023_exam1'),
    ]

    operations = [
        migrations.AddField(
            model_name='classtest',
            name='exam',
            field=models.ForeignKey(to='academics.Exam1', null=True),
        ),
    ]
