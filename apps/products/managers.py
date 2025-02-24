from django.db import models


class RelatedProductManager(models.Manager):

    def get_queryset(self):
        return super(RelatedProductManager, self).get_queryset()\
            .select_related('category')\
            .select_related('manufacturer')\
            .prefetch_related('instances')
