# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2019-06-30 11:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='image',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales', to='sales.SaleImage'),
        ),
    ]
