# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2019-08-26 13:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0021_auto_20190825_1932'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productinstance',
            name='measure_count',
        ),
        migrations.RemoveField(
            model_name='productinstance',
            name='measure_value',
        ),
        migrations.AddField(
            model_name='productinstance',
            name='capacity_type',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Тип ёмкости'),
        ),
        migrations.AddField(
            model_name='productinstance',
            name='measure',
            field=models.IntegerField(default=1, verbose_name='Количество в миллилитрах'),
            preserve_default=False,
        ),
    ]
