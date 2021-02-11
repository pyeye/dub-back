from django.core.management.base import BaseCommand
from apps.products import elastic
from apps.products.models import ProductInfo


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        elastic.delete_index()
        elastic.create_index()
        products = ProductInfo.objects.all()
        for product in products:
            elastic.index_products(product)