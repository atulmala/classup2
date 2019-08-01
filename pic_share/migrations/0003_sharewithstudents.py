# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0011_auto_20190530_1657'),
        ('academics', '0029_auto_20190220_1423'),
        ('pic_share', '0002_imagevideo_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShareWithStudents',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image_video', models.ForeignKey(to='pic_share.ImageVideo')),
                ('section', models.ForeignKey(to='academics.Section')),
                ('student', models.ForeignKey(to='student.Student')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
    ]
