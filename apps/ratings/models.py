from decimal import Decimal

from django.db import models
from django.contrib.postgres.fields import JSONField

from apps.customers.models import Customer
from apps.products.models import Product


class CustomerRating(models.Model):

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=False, null=False, related_name='customer_rating', verbose_name='Покупатель')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=False, null=False, related_name='product_rating', verbose_name='Товар')
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=Decimal('0.0'), verbose_name='Оценка')
    extra = JSONField(blank=True, null=True, default=dict, verbose_name='Дополнительно')

    def __str__(self):
        return str(self.rating)

    class Meta:
        verbose_name = 'Пользовательские оценки'
        verbose_name_plural = 'Пользовательская оценка'
        unique_together = ('product', 'customer')