# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0013_additionaldetails_date_of_admission'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeeDefaulters',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount_due', models.DecimalField(max_digits=10, decimal_places=2)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
