import uuid
import datetime

from django.db import models
from django.contrib.postgres.fields import JSONField
from slugify import slugify

from .managers import RelatedProductManager


def upload_location(instance, filename):
    now = datetime.datetime.now()
    return "product/{year}/{filename}".format(year=now.year, filename=filename)


def upload_category_location(instance, filename):
    code = slugify(instance.name, only_ascii=True)
    filename = uuid.uuid4().hex + '.jpg'
    return "category/{code}/{filename}".format(code=code, filename=filename)


def upload_collection_location(instance, filename):
    filename = uuid.uuid4().hex + '.jpg'
    now = datetime.datetime.now()
    return "collection/{year}/{filename}".format(year=now.year, filename=filename)


class ProductInfo(models.Model):
    name = models.CharField(max_length=255, null=False,  blank=False, verbose_name='Название')
    manufacturer = models.ForeignKey('Manufacturer', on_delete=models.CASCADE, null=False,  blank=False, related_name='product_info', verbose_name='Производитель')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=False,  blank=False, related_name='menu', verbose_name='Категория')
    sfacets = models.ManyToManyField('SFacetValue', blank=True,  verbose_name='парамеры')
    nfacets = models.ManyToManyField('NFacetValue', blank=True,  verbose_name='парамеры')
    tags = models.ManyToManyField('Tags', blank=True, verbose_name='Тэги')
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')

    objects = models.Manager()
    related_objects = RelatedProductManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Описание товара'
        verbose_name_plural = 'Описание товаров'
    
    @property
    def name_slug(self):
        return slugify(self.name, only_ascii=True)

    @property
    def is_active(self):
        return any([instance.status == ProductInstance.STATUS_ACTIVE for instance in self.instances.all()])


class ProductImage(models.Model):
    instance = models.ForeignKey('ProductInstance', on_delete=models.CASCADE, blank=True, null=True, verbose_name='Товар', related_name='images')
    is_active = models.BooleanField(default=True, verbose_name='Активированно')
    is_main = models.BooleanField(default=False, null=False, blank=True, verbose_name='Главная')
    src = models.ImageField(upload_to=upload_location, null=True, blank=True, verbose_name='Фото')
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')


class ProductInstance(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_DRAFT = 'draft'
    STATUS_ARCHIVE = 'archive'
    PRODUCT_STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Активно'),
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_ARCHIVE, 'Архив'),
    )

    sku = models.BigIntegerField(null=False, blank=False, verbose_name='Артикул')
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, blank=False, null=False, related_name='instances', verbose_name='Инфо')
    measure = models.IntegerField(null=False, blank=False, verbose_name='Количество в миллилитрах')
    price = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, verbose_name='Цена')
    base_price = models.DecimalField(null=False, blank=False, max_digits=10, decimal_places=2, verbose_name='Базовая Цена')
    stock_balance = models.IntegerField(null=False, blank=False, verbose_name='Остаток на складе')
    package_amount = models.IntegerField(null=False, blank=False, verbose_name='Количество в упаковке')
    capacity_type = models.CharField(max_length=255, null=True, blank=True, verbose_name='Тип ёмкости')
    sales = JSONField(blank=True, null=True, default=list)
    collections = JSONField(blank=True, null=True, default=list)
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')
    status = models.CharField(max_length=128, choices=PRODUCT_STATUS_CHOICES, default=STATUS_DRAFT)

    def __str__(self):
        return str(self.sku)

    @property
    def is_active(self):
        return self.status == STATUS_ACTIVE

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


class Category(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    slug = models.CharField(max_length=128, null=False, blank=False, verbose_name='Код')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    image = models.ImageField(upload_to=upload_category_location, null=True, blank=True, verbose_name='Фото')
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Manufacturer(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    slug = models.CharField(max_length=128, null=True, blank=True, verbose_name='slug')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')

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
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Метка'
        verbose_name_plural = 'Метки'


class SFacet(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    slug = models.CharField(max_length=128, null=False, unique=True, blank=False, verbose_name='Код')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Строковый аттрибут'
        verbose_name_plural = 'Строковые аттрибуты'


class SFacetValue(models.Model):
    facet = models.ForeignKey(SFacet, related_name='values', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=False, verbose_name='Значение')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')

    class Meta:
        verbose_name = 'Значение аттрибута'
        verbose_name_plural = 'Значения аттрибутов'
        unique_together = ['facet', 'name']


class NFacet(models.Model):
    name = models.CharField(max_length=255, null=False, unique=True, blank=False, verbose_name='Название')
    slug = models.CharField(max_length=128, null=False, unique=True, blank=False, verbose_name='Код')
    suffix = models.CharField(max_length=128, null=True, blank=True, verbose_name='Суффикс')
    is_active = models.BooleanField(null=False, blank=True, default=True, verbose_name='Активированно')
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Числовой аттрибут'
        verbose_name_plural = 'Числовые аттрибуты'


class NFacetValue(models.Model):
    facet = models.ForeignKey(NFacet, related_name='values', on_delete=models.CASCADE)
    #product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE)
    value = models.DecimalField(null=False, blank=False, max_digits=15, decimal_places=5)
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')

    class Meta:
        verbose_name = 'Числовой аттрибут'
        verbose_name_plural = 'Числовой аттрибуты'


class Collection(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(blank=True, default=True)
    is_public = models.BooleanField(blank=True, default=False)
    on_home = models.BooleanField(default=False, null=False, blank=True)
    image = models.OneToOneField('CollectionImage', on_delete=models.SET_NULL, null=True)
    products = models.ManyToManyField(ProductInstance, blank=True, related_name="collections_set")
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    extra = JSONField(blank=True, null=True, default=dict)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name, only_ascii=True)
        super(Collection, self).save(*args, **kwargs)


class CollectionImage(models.Model):
    src = models.ImageField(upload_to=upload_collection_location, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True)
    extra = JSONField(blank=True, null=True, default=dict)



