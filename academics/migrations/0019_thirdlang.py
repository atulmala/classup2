# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_dob'),
        ('academics', '0018_auto_20171001_0000'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThirdLang',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('student', models.ForeignKey(to='student.Student')),
                ('third_lang', models.ForeignKey(to='academics.Subject')),
            ],
        ),
    ]
