from django.core.management.base import BaseCommand
from apps.products import elastic


class Command(BaseCommand):

    def handle(self, *args, **options):
        pass