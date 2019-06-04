from django.core.management.base import BaseCommand
from apps.products.elastic import create_product_index

class Command(BaseCommand):

    def handle(self, *args, **options):
        create_product_index()