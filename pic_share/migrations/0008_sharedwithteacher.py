# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0016_staff'),
        ('pic_share', '0007_auto_20190822_1007'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedWithTeacher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image_video', models.ForeignKey(to='pic_share.ImageVideo')),
                ('staff', models.ForeignKey(to='teacher.Staff', null=True)),
                ('teacher', models.ForeignKey(to='teacher.Teacher', null=True)),
            ],
        ),
    ]
