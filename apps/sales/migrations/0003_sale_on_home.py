# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2019-07-10 19:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0002_auto_20190630_1125'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='on_home',
            field=models.BooleanField(default=False),
        ),
    ]
