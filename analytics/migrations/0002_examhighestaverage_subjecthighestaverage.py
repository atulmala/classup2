# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0030_termtestresult_multi_asses_marks'),
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamHighestAverage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('highest', models.DecimalField(max_digits=6, decimal_places=2)),
                ('average', models.DecimalField(max_digits=6, decimal_places=2)),
                ('exam', models.ForeignKey(to='academics.Exam')),
                ('section', models.ForeignKey(to='academics.Section')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
        migrations.CreateModel(
            name='SubjectHighestAverage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('highest', models.DecimalField(max_digits=6, decimal_places=2)),
                ('average', models.DecimalField(max_digits=6, decimal_places=2)),
                ('exam', models.ForeignKey(to='academics.Exam')),
                ('section', models.ForeignKey(to='academics.Section')),
                ('subject', models.ForeignKey(to='academics.Subject')),
                ('the_class', models.ForeignKey(to='academics.Class')),
            ],
        ),
    ]
