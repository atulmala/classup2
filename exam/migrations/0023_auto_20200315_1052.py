# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0013_additionaldetails_date_of_admission'),
        ('academics', '0031_subject_grade_based'),
        ('exam', '0022_cbserollno'),
    ]

    operations = [
        migrations.CreateModel(
            name='Compartment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('student', models.ForeignKey(to='student.Student')),
                ('subject', models.ForeignKey(to='academics.Subject')),
            ],
        ),
        migrations.AddField(
            model_name='examresult',
            name='exact_status',
            field=models.CharField(default=b'Promoted', max_length=50),
        ),
    ]
