# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0017_auto_20190823_1233'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teachermessagerecord',
            name='sent_to',
            field=models.CharField(max_length=50),
        ),
    ]
