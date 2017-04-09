# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0007_homework'),
    ]

    operations = [
        migrations.CreateModel(
            name='HW',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('teacher', models.CharField(max_length=50)),
                ('the_class', models.CharField(max_length=10)),
                ('section', models.CharField(max_length=10)),
                ('subject', models.CharField(max_length=100)),
                ('creation_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('due_date', models.DateField()),
                ('notes', models.CharField(max_length=200)),
                ('location', models.FileField(upload_to=b'homework/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='homework',
            name='creation_date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
