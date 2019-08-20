# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pic_share', '0005_imagevideo_short_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagevideo',
            name='teacher',
            field=models.ForeignKey(to='teacher.Teacher', null=True),
        ),
    ]
