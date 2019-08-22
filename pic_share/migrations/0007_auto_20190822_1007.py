# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pic_share', '0006_auto_20190820_0957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagevideo',
            name='section',
            field=models.ForeignKey(to='academics.Section', null=True),
        ),
        migrations.AlterField(
            model_name='imagevideo',
            name='the_class',
            field=models.ForeignKey(to='academics.Class', null=True),
        ),
    ]
