import time

from django.test import TestCase
from rest_framework.test import APIClient
from django.conf import settings
from django.http import QueryDict

from .elastic import es, create_index, index_products
from .serializers import ProductCreateSerializer, QuerySerializer
from .models import (
    ProductInfo,
    Manufacturer,
    Category,
    ProductInstance,
    ProductImage,
    SFacet,
    SFacetValue,
    NFacet,
    NFacetValue,
)


class ProductAPITestCase(TestCase):
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
            extra={"name_locale": "абадае дес", "style_locale": "эль"},
        )

        facets_data = [
            {
                "slug": "style",
                "name": "Стиль",
                "values": [{"pk": 139, "name": "Belgian Strong Ale"}],
            },
            {
                "slug": "type",
                "name": "Тип",
                "values": [
                    {"pk": 775, "name": "темное нефильтрованное пастеризованное"}
                ],
            },
            {
                "slug": "composition",
                "name": "Состав",
                "values": [
                    {"pk": 13, "name": "хмель"},
                    {"pk": 14, "name": "дрожжи"},
                    {"pk": 95, "name": "солод"},
                ],
            },
            {
                "slug": "taste",
                "name": "Вкус",
                "values": [
                    {"pk": 15, "name": "сложный"},
                    {"pk": 81, "name": "фруктовый"},
                    {"pk": 82, "name": "ореховый"},
                    {"pk": 63, "name": "дрожжевой"},
                ],
            },
            {
                "slug": "country",
                "name": "Регион",
                "values": [{"pk": 23, "name": "германия"}],
            },
        ]
        facets_data2 = [
            {
                "slug": "style",
                "name": "Стиль",
                "values": [{"pk": 139, "name": "Belgian Strong Ale"}],
            },
            {
                "slug": "type",
                "name": "Тип",
                "values": [
                    {"pk": 775, "name": "нефильтрованное пастеризованное осветленное"}
                ],
            },
            {
                "slug": "composition",
                "name": "Состав",
                "values": [
                    {"pk": 32, "name": "сахар"},
                    {"pk": 11, "name": "вода"},
                    {"pk": 13, "name": "хмель"},
                ],
            },
            {
                "slug": "taste",
                "name": "Вкус",
                "values": [
                    {"pk": 160, "name": "шоколадный"},
                    {"pk": 136, "name": "ванильный"},
                    {"pk": 15, "name": "сложный"},
                    {"pk": 81, "name": "фруктовый"},
                ],
            },
            {
                "slug": "country",
                "name": "Регион",
                "values": [{"pk": 138, "name": "бельгия"}],
            },
        ]

        for facet_data, facet_data2 in zip(facets_data, facets_data2):
            s_facet = SFacet.objects.create(
                name=facet_data["name"],
                slug=facet_data["slug"],
                is_active=True,
            )
            for value in facet_data["values"]:
                s_facet_value, created = SFacetValue.objects.get_or_create(
                    facet=s_facet,
                    name=value["name"],
                    is_active=True,
                )
                product_info.sfacets.add(s_facet_value)

            for value2 in facet_data2["values"]:
                s_facet_value2, created = SFacetValue.objects.get_or_create(
                    facet=s_facet,
                    name=value2["name"],
                    is_active=True,
                )
                product_info2.sfacets.add(s_facet_value2)

        n_facets_data = [
            {"slug": "density", "name": "Плотность", "value": 22.0, "suffix": "%"},
            {"slug": "strength", "name": "Крепость", "value": 9.5, "suffix": "%"},
        ]
        n_facets_data2 = [
            {"slug": "density", "name": "Плотность", "value": 20.0, "suffix": "%"},
            {"slug": "strength", "name": "Крепость", "value": 8.5, "suffix": "%"},
        ]

        for n_facet_data, n_facet_data2 in zip(n_facets_data, n_facets_data2):
            n_facet = NFacet.objects.create(
                name=n_facet_data["name"],
                slug=n_facet_data["slug"],
                suffix=n_facet_data["suffix"],
                is_active=True,
            )
            n_facet_value = NFacetValue.objects.create(
                facet=n_facet,
                value=n_facet_data["value"],
            )

            n_facet_value2 = NFacetValue.objects.create(
                facet=n_facet,
                value=n_facet_data2["value"],
            )

            product_info.nfacets.add(n_facet_value)
            product_info2.nfacets.add(n_facet_value2)

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

        ProductInstance.objects.create(
            sku=8974385,
            product_info=product_info2,
            measure=5000,
            price=1550.00,
            base_price=1550.00,
            stock_balance=50,
            package_amount=1,
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

    def test_base_products(self):
        response = self.client.get("/v1/products/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertEqual(len(data["items"]), 3)
        self.assertEqual(data["total"], 3)

    def test_detail_info(self):
        response = self.client.get("/v1/products/1/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Abbaye Des Rocs Grand Cru")

    def test_detail_multiple_instances(self):
        response = self.client.get("/v1/products/2/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("count_instances", data)
        self.assertIn("instances", data)
        self.assertEqual(data["count_instances"], 2)
        self.assertEqual(len(data["instances"]), 2)

    def test_detail_info_404(self):
        response = self.client.get("/v1/products/3/")
        self.assertEqual(response.status_code, 404)

    def test_detail_instance(self):
        response = self.client.get("/v1/products/instances/1/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["instance"]["pk"], 1)

    def test_detail_instance_404(self):
        response = self.client.get("/v1/products/instances/5/")
        self.assertEqual(response.status_code, 404)

    def test_filter_nfacets(self):
        response = self.client.get("/v1/products/?nfacets[]=density:20-21")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 2)
        for product in data["items"]:
            density_values = [
                float(facet["value"])
                for facet in product["number_facets"]
                if facet["slug"] == "density"
            ]
            self.assertEqual(len(density_values), 1)
            self.assertTrue(20 <= density_values[0] <= 21)

    def test_filter_nfacets_empty(self):
        response = self.client.get("/v1/products/?nfacets[]=density:200-210")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 0)

    def test_filter_sfacet(self):
        response = self.client.get("/v1/products/?sfacets[]=country:15")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        country_value = [
            facet["values"]
            for facet in data["items"][0]["string_facets"]
            if facet["slug"] == "country"
        ][0]
        self.assertEqual(len(country_value), 1)
        self.assertEqual(country_value[0], {"pk": 15, "name": "германия"})

    def test_filter_multiple_sfacet(self):
        response = self.client.get("/v1/products/?sfacets[]=country:15,16")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 3)

    def test_filter_multiple_sfacets(self):
        response = self.client.get(
            "/v1/products/?sfacets[]=style:1&sfacets[]=taste:9,10&nfacets[]=density:20-22"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 3)

    def test_all_values_sfacet(self):
        response = self.client.get("/v1/facet/full/?sfacet=country")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual({'германия', 'бельгия'}, {item["name"] for item in response.data})

    def test_all_values_sfacet_empty(self):
        response = self.client.get("/v1/facet/full/")
        self.assertEqual(response.status_code, 400)

    def test_base_facet(self):
        response = self.client.get("/v1/facets/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("sfacets", response.data)
        self.assertIn("nfacets", response.data)
        self.assertEqual(len(response.data["nfacets"]), 2)
        self.assertEqual(len(response.data["sfacets"]), 5)
        style_values = [
            facet["values"]
            for facet in response.data["sfacets"]
            if facet["slug"] == "style"
        ][0]
        self.assertEqual(len(style_values), 1)
        self.assertEqual(style_values[0]["count"], 3)
        country_values = [
            facet["values"]
            for facet in response.data["sfacets"]
            if facet["slug"] == "country"
        ][0]
        self.assertEqual(len(country_values), 2)
        self.assertEqual(country_values[0]["count"], 2)
        self.assertEqual(country_values[1]["count"], 1)

    def test_facet_special(self):
        """
        Проверка на наличие всех вариантов фильтров.
        Первый фильтр country идет от выбранной 15, второй от попадания в выборку товаров от taste 9
        """
        response = self.client.get("/v1/facets/?sfacets[]=country:15&sfacets[]=taste:9")
        country_values = [
            facet["values"]
            for facet in response.data["sfacets"]
            if facet["slug"] == "country"
        ][0]
        self.assertEqual(len(country_values), 2)

    def test_facet_multiselect_for_one(self):
        """После фильтров попадет только один товар, поэтому фильтр по country будет один"""
        response = self.client.get("/v1/facets/?sfacets[]=country:15&sfacets[]=type:2")
        country_values = [
            facet["values"]
            for facet in response.data["sfacets"]
            if facet["slug"] == "country"
        ][0]
        self.assertEqual(len(country_values), 1)

    def test_product_create(self):
        products = ProductInfo.objects.all()
        product_instances = ProductInstance.objects.all()
        self.assertEqual(len(products), 2)
        self.assertEqual(len(product_instances), 3)
        image = ProductImage.objects.create(
            is_main = True,
            src = 'image.png',
        )
        data = {
            "name": "test",
            "description": "description",
            "category": 1,
            "manufacturer": 1,
            "tags": [],
            "nfacets": [1],
            "sfacets": [1, 2],
            "instances": [],
        }
        product = ProductCreateSerializer(data=data)
        self.assertFalse(product.is_valid())
        data["instances"] = [
            {
                "sku": 999999,
                "measure": 25,
                "base_price": 200,
                "status": "active",
                "stock_balance": 2,
                "package_amount": 5,
                "images": [image.pk],
            }
        ]
        product = ProductCreateSerializer(data=data)
        self.assertTrue(product.is_valid())
        product.save()
        products = ProductInfo.objects.all()
        product_instances = ProductInstance.objects.all()
        self.assertEqual(len(products), 3)
        self.assertEqual(len(product_instances), 4)


class QuerySerializerTests(TestCase):
    def test_valid_data(self):
        query_string = "category=beer&nfacets[]=density:8-20&nfacets[]=strength:5.5-10&sfacets[]=country:138,23&sfacets[]=composition:95,32&page=3&sort=price-desc&tags=1,2,3&sales=5,10,15&collections=101,102"
        query_dict = QueryDict(query_string, mutable=True)
        serializer = QuerySerializer(data=query_dict)
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['page'], 3)
        self.assertEqual(validated_data['sort'], ('price', 'desc'))
        self.assertEqual(validated_data['tags'], (1, 2, 3))
        self.assertEqual(validated_data['sales'], (5, 10, 15))
        self.assertEqual(validated_data['collections'], (101, 102))
        self.assertEqual(validated_data['sfacets'], [('country', (138, 23)), ('composition', (95, 32))])
        self.assertEqual(validated_data['nfacets'], [('density', (8, 20)), ('strength', (5.5, 10))])

    def test_invalid_sort(self):
        query_string = "sort=price-descending"
        data = QueryDict(query_string, mutable=True)
        # data = {'order': 'price-descending'}
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('sort', serializer.errors)

    def test_invalid_tags(self):
        query_string = "tags=1,2,a"
        data = QueryDict(query_string, mutable=True)
        # data = {'tags': '1,2,a'}
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tags', serializer.errors)

    def test_invalid_sales(self):
        query_string = "sales=10,,20"
        data = QueryDict(query_string, mutable=True)
        # data = {'sales': '10,,20'}
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('sales', serializer.errors)

    def test_missing_page(self):
        query_string = ""
        data = QueryDict(query_string, mutable=True)
        # data = {}
        serializer = QuerySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['page'], 1)

    def test_invalid_sfacets(self):
        query_string = "sfacets[]=attr1:1,2&sfacets[]=attr2:"
        data = QueryDict(query_string, mutable=True)
        # data = {'sfacets': ['attr1:1,2', 'attr2:']}
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('sfacets', serializer.errors)

    def test_invalid_nfacets_format(self):
        query_string = "nfacets[]=price:1,100"
        data = QueryDict(query_string, mutable=True)
        # data = {'nfacets': ['price:10,100', 'stock:five-50']}
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nfacets', serializer.errors)

    def test_invalid_nfacets_values(self):
        query_string = "nfacets[]=stock:five-50"
        data = QueryDict(query_string, mutable=True)
        # data = {'nfacets': ['price:10-ten']}
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('nfacets', serializer.errors)

    def test_empty_sales(self):
        query_string = "sales="
        data = QueryDict(query_string, mutable=True)
        # data = {'sales': ''}
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIsNone(serializer.validated_data.get('sales', None))

    def test_empty_sfacets(self):
        query_string = "sfacets[]="
        data = QueryDict(query_string, mutable=True)
        # data = {'sfacets': []}
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIsNone(serializer.validated_data.get('sfacets', None))

    def test_empty_nfacets(self):
        query_string = "nfacets[]="
        data = QueryDict(query_string, mutable=True)
        # data = {'nfacets': []}
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIsNone(serializer.validated_data.get('nfacets', None))
