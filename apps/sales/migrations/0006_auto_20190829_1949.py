# Generated by Django 2.2.4 on 2019-08-29 19:49

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0005_auto_20190826_1806'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categorysale',
            name='extra',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно'),
        ),
        migrations.AlterField(
            model_name='collectionsale',
            name='extra',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно'),
        ),
        migrations.AlterField(
            model_name='productsale',
            name='extra',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно'),
        ),
        migrations.AlterField(
            model_name='sale',
            name='extra',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно'),
        ),
        migrations.AlterField(
            model_name='sale',
            name='is_active',
            field=models.BooleanField(blank=True, default=True, verbose_name='Активировано'),
        ),
        migrations.AlterField(
            model_name='sale',
            name='on_home',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='saleimage',
            name='extra',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно'),
        ),
    ]
