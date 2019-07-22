# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0029_auto_20190220_1423'),
        ('teacher', '0016_staff'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImageVideo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('descrition', models.CharField(max_length=200)),
                ('location', models.ImageField(upload_to=b'image_video/')),
                ('section', models.ForeignKey(to='academics.Section')),
                ('teacher', models.ForeignKey(to='teacher.Teacher')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
    ]
