# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0013_auto_20170604_1353'),
    ]

    operations = [
        migrations.CreateModel(
            name='TermTestResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('periodic_test_marks', models.DecimalField(default=0.0, max_digits=6, decimal_places=2)),
                ('note_book_marks', models.DecimalField(default=0.0, max_digits=6, decimal_places=2)),
                ('sub_enrich_marks', models.DecimalField(default=0.0, max_digits=6, decimal_places=2)),
                ('test_result', models.ForeignKey(to='academics.TestResults')),
            ],
        ),
        migrations.AddField(
            model_name='classtest',
            name='syllabus',
            field=models.CharField(default=b' ', max_length=200),
        ),
        migrations.AlterField(
            model_name='classtest',
            name='test_type',
            field=models.CharField(default=b'Unit', max_length=200),
        ),
    ]
