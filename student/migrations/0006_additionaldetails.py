# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0005_auto_20180204_1552'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalDetails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mother_name', models.CharField(default=b'Not Available', max_length=50)),
                ('address', models.CharField(default=b' ', max_length=200)),
                ('adhar', models.CharField(default=b'Not Available', max_length=30)),
                ('blood_group', models.CharField(default=b'Not Available', max_length=10)),
                ('father_occupation', models.CharField(default=b'Not Available', max_length=100)),
                ('mother_occupation', models.CharField(default=b'Not Available', max_length=100)),
                ('student', models.ForeignKey(to='student.Student')),
            ],
        ),
    ]
