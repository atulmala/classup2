# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lectures', '0002_lecture_creation_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='lecture',
            name='doc_file',
            field=models.FileField(null=True, upload_to=b'image_video/'),
        ),
    ]
