import time

from django.test import TestCase
from rest_framework.test import APIClient
from django.conf import settings

from apps.products.elastic import es, create_index, index_products
from apps.products.models import (
    ProductInfo,
    Manufacturer,
    Category,
    ProductInstance,
    SFacet,
    SFacetValue,
    NFacet,
    NFacetValue,
)


class SearchAPITestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        create_index()

        manufacturer = Manufacturer.objects.create(
            name="ayinger", slug="Ayinger", is_active=True
        )
        category = Category.objects.create(name="Пиво", slug="beer", is_active=True)
        product_info = ProductInfo.objects.create(
            name="Abbaye Des Rocs Grand Cru",
            manufacturer=manufacturer,
            description="Grand Cru — бельгийский крепкий эль...",
            category=category,
            extra={"name_locale": "абадае дес", "style_locale": "эль"},
        )
        product_info2 = ProductInfo.objects.create(
            name="De Ranke Noir De Dottignie",
            manufacturer=manufacturer,
            description="De Ranke Noir De Dottignie — бельгийский эль",
            category=category,
            extra={"name_locale": "де ранке ноар", "style_locale": "эль"},
        )

        ProductInstance.objects.create(
            sku=8974383,
            product_info=product_info,
            measure=750,
            price=950.00,
            base_price=950.00,
            stock_balance=751,
            package_amount=5,
            status=ProductInstance.STATUS_ACTIVE,
        )
        ProductInstance.objects.create(
            sku=8974384,
            product_info=product_info2,
            measure=500,
            price=550.00,
            base_price=550.00,
            stock_balance=250,
            package_amount=10,
            status=ProductInstance.STATUS_ACTIVE,
        )

        for product in ProductInfo.objects.all():
            index_products(product)

        es.indices.refresh(index=settings.ELASTIC_SEARCH["INDEX"])
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        es.indices.delete(index=settings.ELASTIC_SEARCH["INDEX"], ignore=[400, 404])
        super().tearDownClass()

    def test_search_products(self):
        response = self.client.get("/v1/search/?q=abbaye")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["name"], "Abbaye Des Rocs Grand Cru")

    def test_search_products_fuzzy(self):
        response = self.client.get("/v1/search/?q=abaye")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["items"][0]["name"], "Abbaye Des Rocs Grand Cru")

    def test_search_products_locale(self):
        response = self.client.get("/v1/search/?q=ноар")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(
            response.data["items"][0]["name"], "De Ranke Noir De Dottignie"
        )
