# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('setup', '0019_auto_20171031_2142'),
        ('academics', '0019_thirdlang'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scheme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sequence', models.IntegerField(max_length=2)),
                ('school', models.ForeignKey(to='setup.School')),
                ('subject', models.ForeignKey(to='academics.Subject')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
    ]
