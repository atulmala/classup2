# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_examhighestaverage_subjecthighestaverage'),
    ]

    operations = [
        migrations.AddField(
            model_name='subjectanalysis',
            name='multi_asses_marks',
            field=models.DecimalField(default=0.0, max_digits=6, decimal_places=2),
        ),
        migrations.AddField(
            model_name='subjectanalysis',
            name='periodic_test_marks',
            field=models.DecimalField(default=0.0, max_digits=6, decimal_places=2),
        ),
        migrations.AddField(
            model_name='subjectanalysis',
            name='portfolio_marks',
            field=models.DecimalField(default=0.0, max_digits=6, decimal_places=2),
        ),
        migrations.AddField(
            model_name='subjectanalysis',
            name='prac_marks',
            field=models.DecimalField(null=True, max_digits=6, decimal_places=2),
        ),
        migrations.AddField(
            model_name='subjectanalysis',
            name='sub_enrich_marks',
            field=models.DecimalField(default=0.0, max_digits=6, decimal_places=2),
        ),
        migrations.AddField(
            model_name='subjectanalysis',
            name='total_marks',
            field=models.DecimalField(null=True, max_digits=6, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='subjectanalysis',
            name='marks',
            field=models.DecimalField(default=-5000.0, max_digits=6, decimal_places=2),
        ),
    ]
