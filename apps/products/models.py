import uuid
import datetime

from django.db import models
from django.contrib.postgres.fields import JSONField
from slugify import slugify


def upload_location(instance, filename):
    now = datetime.datetime.now()
    filename = uuid.uuid4().hex + '.jpg'
    return "product/{year}/{filename}".format(year=now.year, filename=filename)

def upload_category_location(instance, filename):
    code = slugify(instance.name, only_ascii=True)
    filename = uuid.uuid4().hex + '.jpg'
    return "category/{code}/{filename}".format(code=code, filename=filename)


class ProductInfo(models.Model):
    ACTIVE = 'active'
    DRAFT = 'draft'
    ARCHIVE = 'archive'
    PRODUCT_STATUS_CHOICES = (
        (ACTIVE, 'Активно'),
        (DRAFT, 'Черновик'),
        (ARCHIVE, 'Архив'),
    )

    name = models.CharField(max_length=255, null=False,  blank=False, verbose_name='Название')
    manufacturer = models.ForeignKey('Manufacturer', null=False,  blank=False, related_name='product_info', verbose_name='Производитель')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    category = models.ForeignKey('Category', null=False,  blank=False, related_name='menu', verbose_name='Категория')
    sfacets = models.ManyToManyField('SFacetValue', blank=True,  verbose_name='парамеры')
    nfacets = models.ManyToManyField('NFacet', blank=True,  through='NFacetValue', verbose_name='парамеры')
    tags = models.ManyToManyField('Tags', blank=True, verbose_name='Тэги')
    status = models.CharField(max_length=128, choices=PRODUCT_STATUS_CHOICES, default=DRAFT)
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Описание товара'
        verbose_name_plural = 'Описание товаров'


class ProductImage(models.Model):
    instance = models.ForeignKey('ProductInstance', blank=True, null=True, verbose_name='Товар', related_name='images')
    is_active = models.BooleanField(default=True, verbose_name='Активированно')
    is_main = models.BooleanField(default=False, null=False, blank=True, verbose_name='Главная')
    src = models.ImageField(upload_to=upload_location, null=True, blank=True, verbose_name='Фото')
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')


class ProductInstance(models.Model):
    sku = models.IntegerField(null=False, blank=False, verbose_name='Артикул')
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, blank=False, null=False, related_name='instances', verbose_name='Инфо')
    measure_count = models.CharField(max_length=128, null=False, blank=False, verbose_name='Количество (250/0.75)')
    measure_value = models.CharField(max_length=128, null=False, blank=False, verbose_name='Ед. измерения (гр./шт./л./мл./на чаше')
    price = models.DecimalField(null=False, blank=False, max_digits=10, decimal_places=2, verbose_name='Цена')
    stock_balance = models.IntegerField(null=False, blank=False, verbose_name='Остаток на складе')
    package_amount = models.IntegerField(null=False, blank=False, verbose_name='Количество в упаковке')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')
    is_active = models.BooleanField(default=True, null=False, blank=True, verbose_name='Активированно')

    def __str__(self):
        return self.sku

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'




class Category(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    slug = models.CharField(max_length=128, null=False, blank=False, verbose_name='Код')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    image = models.ImageField(upload_to=upload_category_location, null=True, blank=True, verbose_name='Фото')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
"ProductInstance.images"


class Manufacturer(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    slug = models.CharField(max_length=128, null=True, blank=True, verbose_name='slug')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name, only_ascii=True)
        super(Manufacturer, self).save(*args, **kwargs)


class Tags(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Метка'
        verbose_name_plural = 'Метки'


class SFacet(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    slug = models.CharField(max_length=128, null=False, unique=True, blank=False, verbose_name='Код')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Строковый аттрибут'
        verbose_name_plural = 'Строковые аттрибуты'


class SFacetValue(models.Model):
    facet = models.ForeignKey(SFacet, related_name='values', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name='Значение')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    class Meta:
        verbose_name = 'Значение аттрибута'
        verbose_name_plural = 'Значения аттрибутов'
        unique_together = ['facet', 'name']


class NFacet(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    slug = models.CharField(max_length=128, null=False, unique=True, blank=False, verbose_name='Код')
    suffix = models.CharField(max_length=128, null=True, blank=True, verbose_name='Суффикс')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Числовой аттрибут'
        verbose_name_plural = 'Числовые аттрибуты'


class NFacetValue(models.Model):
    facet = models.ForeignKey(NFacet, related_name='values', on_delete=models.CASCADE)
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE)
    value = models.DecimalField(null=False, blank=False, max_digits=15, decimal_places=5)
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    class Meta:
        verbose_name = 'Числовой аттрибут'
        verbose_name_plural = 'Числовой аттрибуты'



