# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0001_initial'),
        ('setup', '0001_initial'),
        ('academics', '0002_auto_20160817_1644'),
    ]

    operations = [
        migrations.AddField(
            model_name='teachersubjects',
            name='teacher',
            field=models.ForeignKey(to='teacher.Teacher'),
        ),
        migrations.AddField(
            model_name='subject',
            name='school',
            field=models.ForeignKey(to='setup.School'),
        ),
        migrations.AddField(
            model_name='section',
            name='school',
            field=models.ForeignKey(to='setup.School'),
        ),
        migrations.AddField(
            model_name='exam',
            name='school',
            field=models.ForeignKey(to='setup.School'),
        ),
        migrations.AddField(
            model_name='classtest',
            name='school',
            field=models.ForeignKey(to='setup.School'),
        ),
        migrations.AddField(
            model_name='classtest',
            name='section',
            field=models.ForeignKey(to='academics.Section'),
        ),
        migrations.AddField(
            model_name='classtest',
            name='subject',
            field=models.ForeignKey(to='academics.Subject'),
        ),
        migrations.AddField(
            model_name='classtest',
            name='teacher',
            field=models.ForeignKey(to='teacher.Teacher'),
        ),
        migrations.AddField(
            model_name='classtest',
            name='the_class',
            field=models.ForeignKey(to='academics.Class'),
        ),
        migrations.AddField(
            model_name='classteacher',
            name='class_teacher',
            field=models.ForeignKey(to='teacher.Teacher'),
        ),
        migrations.AddField(
            model_name='classteacher',
            name='school',
            field=models.ForeignKey(to='setup.School'),
        ),
        migrations.AddField(
            model_name='classteacher',
            name='section',
            field=models.ForeignKey(to='academics.Section'),
        ),
        migrations.AddField(
            model_name='classteacher',
            name='standard',
            field=models.ForeignKey(to='academics.Class'),
        ),
        migrations.AddField(
            model_name='class',
            name='school',
            field=models.ForeignKey(to='setup.School'),
        ),
    ]
