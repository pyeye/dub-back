import uuid
import datetime

from django.contrib.postgres.fields import JSONField, DateTimeRangeField
from django.db import models

from apps.products.models import Category, Collection, ProductInstance


SALE_TYPES = ['condition', 'percent', 'fixed']


def upload_location(instance, filename):
    filename = uuid.uuid4().hex + '.jpg'
    now = datetime.datetime.now()
    return "sales/{year}/{filename}".format(year=now.year, filename=filename)


class Sale(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    details = JSONField()
    image = models.OneToOneField('SaleImage', on_delete=models.SET_NULL, null=True, related_name='sales')
    date_start = models.DateField()
    date_end = models.DateField()
    categories = models.ManyToManyField(Category, through='CategorySale', blank=True, null=True)
    collections = models.ManyToManyField(Collection, through='CollectionSale', blank=True, null=True)
    products = models.ManyToManyField(ProductInstance, through='ProductSale',  blank=True, null=True)
    created_at = models.DateField(auto_now_add=True, blank=True)
    updated_at = models.DateField(auto_now=True, blank=True)
    is_active = models.BooleanField(default=True, null=False, blank=True, verbose_name='Активировано')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'


class CategorySale(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    details = JSONField(blank=True, null=True)
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')


class CollectionSale(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    details = JSONField(blank=True, null=True)
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')


class ProductSale(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductInstance, on_delete=models.CASCADE)
    details = JSONField(blank=True, null=True)
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')


class SaleImage(models.Model):
    src = models.ImageField(upload_to=upload_location, null=True, blank=True, verbose_name='Фото')
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')
    extra = JSONField(blank=True, null=True, default={}, verbose_name='Дополнительно')
