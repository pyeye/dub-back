import uuid
import datetime
from decimal import Decimal

from django.contrib.postgres.fields import JSONField, DateTimeRangeField
from django.db import models

from apps.products.models import Category, Collection, ProductInstance
from apps.base.utils import localize_month
from . import elastic


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
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    categories = models.ManyToManyField(Category, through='CategorySale', blank=True)
    collections = models.ManyToManyField(Collection, through='CollectionSale', blank=True)
    products = models.ManyToManyField(ProductInstance, through='ProductSale',  blank=True)
    created_at = models.DateField(auto_now_add=True, blank=True)
    updated_at = models.DateField(auto_now=True, blank=True)
    is_active = models.BooleanField(default=True, null=False, blank=True, verbose_name='Активировано')
    on_home = models.BooleanField(default=False, null=False, blank=True)
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'
    
    @property
    def in_process(self):
        today = datetime.datetime.today()
        return today > self.date_start and today < self.date_end

    @property
    def fdate_start(self):
        date = self.date_start
        return self._format_date(date)

    @property
    def fdate_end(self):
        date = self.date_end
        return self._format_date(date)

    def _format_date(self, date):
        return {
            'day': date.day,
            'month': localize_month(date.month),
            'year': date.year,
        }
    
    def update_product_instances(self):
        product_instances = dict()
        sale_info = {
            'pk': self.pk,
            'name': self.name,
            'date_start': self.date_start.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'date_end': self.date_end.strftime('%Y-%m-%dT%H:%M:%S%z'),
        }

        for collection_set in self.collectionsale_set.all():
            for collection_product in collection_set.collection.products.all():
                details = collection_set.details if collection_set.details else self.details
                sale = {**sale_info, **details}
                collection_product.sales.append(sale)
                collection_product.price = self._get_price(collection_product.base_price, collection_product.sales)
                product_instances[collection_product.pk] = collection_product
        
        for product_set in self.productsale_set.all():
            details = product_set.details if product_set.details else self.details
            sale = {**sale_info, **details}
            product_set.product.sales.append(sale)
            product_set.product.price = self._get_price(product_set.product.base_price, product_set.product.sales)
            product_instances[product_set.product.pk] = product_set.product
        
        product_instances = list(product_instances.values())
        es_product_instances = [
            {'product_pk': instance.product_info.pk, 'instance_pk': instance.pk, 'sales': instance.sales, 'price': instance.price} 
            for instance 
            in product_instances
        ]

        ProductInstance.objects.bulk_update(product_instances, ['sales', 'price'])
        elastic.add_sale(es_product_instances)
    
    def delete_product_instances(self):
        es_product_instances = list()
        instances = ProductInstance.objects.filter(sales__contains=[{'pk': self.pk}])
        for instance in instances:
            sales = [sale for sale in instance.sales if sale['pk'] != self.pk]
            price = self._get_price(instance.base_price, sales)
            instance.sales = sales
            instance.price = price
            es_product_instance = {
                'product_pk': instance.product_info.pk,
                'instance_pk': instance.pk,
                'sales': sales,
                'price': price,
            }
            es_product_instances.append(es_product_instance)
        
        ProductInstance.objects.bulk_update(instances, ['sales', 'price'])
        elastic.delete_sale(es_product_instances)
            
    
    def _get_price(self, base_price, sales):
        price = Decimal(base_price)
        sales_with_fixed_price = []
        sales_with_percent_price = []
        for sale in sales:
            if sale['type'] == 'fixed':
                sales_with_fixed_price.append(sale['fixed'])
            if sale['type'] == 'percent':
                sales_with_percent_price.append(sale['percent'])
        if sales_with_fixed_price:
            price = sales_with_fixed_price[-1]
        if sales_with_percent_price:
            percent = Decimal(sales_with_percent_price[-1])
            price = price * ((100 - percent) / 100)
        return self._format_price(price)
    
    def _format_price(self, price):
        return str(int(price)) if price % 1 == 0 else "{:.2f}".format(price)


class CategorySale(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    details = JSONField(blank=True, null=True)
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')


class CollectionSale(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    details = JSONField(blank=True, null=True)
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')


class ProductSale(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductInstance, on_delete=models.CASCADE)
    details = JSONField(blank=True, null=True)
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')


class SaleImage(models.Model):
    src = models.ImageField(upload_to=upload_location, null=True, blank=True, verbose_name='Фото')
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=True, verbose_name='Созданно')
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')
