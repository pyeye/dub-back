# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2019-05-20 16:18
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_auto_20190511_2016'),
    ]

    operations = [
        migrations.CreateModel(
            name='NFacet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('slug', models.CharField(max_length=128, unique=True, verbose_name='Код')),
                ('suffix', models.CharField(blank=True, max_length=128, null=True, verbose_name='Суффикс')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активированно')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True, verbose_name='Дополнительно')),
            ],
            options={
                'verbose_name': 'Числовой аттрибут',
                'verbose_name_plural': 'Числовые аттрибуты',
            },
        ),
        migrations.CreateModel(
            name='NFacetValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=5, max_digits=15)),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True, verbose_name='Дополнительно')),
                ('facet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='products.NFacet')),
            ],
            options={
                'verbose_name': 'Числовой аттрибут',
                'verbose_name_plural': 'Числовой аттрибуты',
            },
        ),
        migrations.CreateModel(
            name='SFacet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('slug', models.CharField(max_length=128, unique=True, verbose_name='Код')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активированно')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True, verbose_name='Дополнительно')),
            ],
            options={
                'verbose_name': 'Строковый аттрибут',
                'verbose_name_plural': 'Строковые аттрибуты',
            },
        ),
        migrations.RenameModel(
            old_name='FacetValue',
            new_name='SFacetValue',
        ),
    ]
