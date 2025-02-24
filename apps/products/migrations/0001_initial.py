# Generated by Django 2.2.4 on 2020-12-08 11:39

import apps.products.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('slug', models.CharField(max_length=128, verbose_name='Код')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('is_active', models.BooleanField(blank=True, default=True, verbose_name='Активированно')),
                ('image', models.ImageField(blank=True, null=True, upload_to=apps.products.models.upload_category_location, verbose_name='Фото')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
            ],
            options={
                'verbose_name_plural': 'Категории',
                'verbose_name': 'Категория',
            },
        ),
        migrations.CreateModel(
            name='CollectionImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('src', models.ImageField(blank=True, null=True, upload_to=apps.products.models.upload_collection_location)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('slug', models.CharField(blank=True, max_length=128, null=True, verbose_name='slug')),
                ('is_active', models.BooleanField(blank=True, default=True, verbose_name='Активированно')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
            ],
            options={
                'verbose_name_plural': 'Производители',
                'verbose_name': 'Производитель',
            },
        ),
        migrations.CreateModel(
            name='NFacet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('slug', models.CharField(max_length=128, unique=True, verbose_name='Код')),
                ('suffix', models.CharField(blank=True, max_length=128, null=True, verbose_name='Суффикс')),
                ('is_active', models.BooleanField(blank=True, default=True, verbose_name='Активированно')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
            ],
            options={
                'verbose_name_plural': 'Числовые аттрибуты',
                'verbose_name': 'Числовой аттрибут',
            },
        ),
        migrations.CreateModel(
            name='NFacetValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=5, max_digits=15)),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
                ('facet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='products.NFacet')),
            ],
            options={
                'verbose_name_plural': 'Числовой аттрибуты',
                'verbose_name': 'Числовой аттрибут',
            },
        ),
        migrations.CreateModel(
            name='ProductInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Описание')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Созданно')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='menu', to='products.Category', verbose_name='Категория')),
                ('manufacturer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_info', to='products.Manufacturer', verbose_name='Производитель')),
                ('nfacets', models.ManyToManyField(blank=True, to='products.NFacetValue', verbose_name='парамеры')),
            ],
            options={
                'verbose_name_plural': 'Описание товаров',
                'verbose_name': 'Описание товара',
            },
        ),
        migrations.CreateModel(
            name='SFacet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('slug', models.CharField(max_length=128, unique=True, verbose_name='Код')),
                ('is_active', models.BooleanField(blank=True, default=True, verbose_name='Активированно')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
            ],
            options={
                'verbose_name_plural': 'Строковые аттрибуты',
                'verbose_name': 'Строковый аттрибут',
            },
        ),
        migrations.CreateModel(
            name='Tags',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Название')),
                ('is_active', models.BooleanField(blank=True, default=True, verbose_name='Активированно')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
            ],
            options={
                'verbose_name_plural': 'Метки',
                'verbose_name': 'Метка',
            },
        ),
        migrations.CreateModel(
            name='SFacetValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Значение')),
                ('is_active', models.BooleanField(blank=True, default=True, verbose_name='Активированно')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
                ('facet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='products.SFacet')),
            ],
            options={
                'verbose_name_plural': 'Значения аттрибутов',
                'verbose_name': 'Значение аттрибута',
                'unique_together': {('facet', 'name')},
            },
        ),
        migrations.CreateModel(
            name='ProductInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.BigIntegerField(verbose_name='Артикул')),
                ('measure', models.IntegerField(verbose_name='Количество в миллилитрах')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Цена')),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Базовая Цена')),
                ('stock_balance', models.IntegerField(verbose_name='Остаток на складе')),
                ('package_amount', models.IntegerField(verbose_name='Количество в упаковке')),
                ('capacity_type', models.CharField(blank=True, max_length=255, null=True, verbose_name='Тип ёмкости')),
                ('sales', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=list, null=True)),
                ('collections', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=list, null=True)),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Созданно')),
                ('status', models.CharField(choices=[('active', 'Активно'), ('draft', 'Черновик'), ('archive', 'Архив')], default='draft', max_length=128)),
                ('product_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='products.ProductInfo', verbose_name='Инфо')),
            ],
            options={
                'verbose_name_plural': 'Товары',
                'verbose_name': 'Товар',
            },
        ),
        migrations.AddField(
            model_name='productinfo',
            name='sfacets',
            field=models.ManyToManyField(blank=True, to='products.SFacetValue', verbose_name='парамеры'),
        ),
        migrations.AddField(
            model_name='productinfo',
            name='tags',
            field=models.ManyToManyField(blank=True, to='products.Tags', verbose_name='Тэги'),
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активированно')),
                ('is_main', models.BooleanField(blank=True, default=False, verbose_name='Главная')),
                ('src', models.ImageField(blank=True, null=True, upload_to=apps.products.models.upload_location, verbose_name='Фото')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Созданно')),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True, verbose_name='Дополнительно')),
                ('instance', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='products.ProductInstance', verbose_name='Товар')),
            ],
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(blank=True, default=True)),
                ('is_public', models.BooleanField(blank=True, default=False)),
                ('on_home', models.BooleanField(blank=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('extra', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('image', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.CollectionImage')),
                ('products', models.ManyToManyField(blank=True, related_name='collections_set', to='products.ProductInstance')),
            ],
        ),
    ]
