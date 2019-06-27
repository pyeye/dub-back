from random import randint
import os
import json
import random
import itertools

from django.core.management.base import BaseCommand
from django.core.files import File
from apps.products import elastic
from apps.products.serializers import ProductCreateSerializer
from apps.products.models import (
    Manufacturer,
    Category,
    Tags,
    SFacet,
    SFacetValue,
    NFacet,
    ProductImage,
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        all_products = self.get_products('all_products/beer.json')
        initial_products = all_products[:1000]
        products_data = []
        for initial_product in initial_products:
            try:
                initial_data = self.get_product_data(initial_product)
            except (ValueError, TypeError, IndexError):
                continue
            products_data.append(initial_data)
        grouped_products = itertools.groupby(products_data, lambda elem: elem['group_by'])
        for index, (group_by, product) in enumerate(grouped_products):
            self.create_product(list(product))

    def get_product_data(self, product_initial):
        measure = self.get_attr('Объем:', product_initial, 'measure', first_only=True)
        if product_initial['title'].startswith('Уманьпиво'):
            raise ValueError
        data = {
            'sku': randint(0, 10000000),
            'name': product_initial['title'].split(',')[0].split(maxsplit=1)[1],
            'category': Category.objects.get(slug='beer'),
            'manufacturer': self.get_attr('Производитель:', product_initial, 'manufacturer', first_only=True),
            'tags': [item.split('/')[0] for item in product_initial['tags']],
            'measure_count': measure['values'].split()[0],
            'measure_value': measure['values'].split()[1],
            'image': product_initial['images'][0]['path'].split('/')[1],
            'price': self.randrange(200, 1000, 50),
            'stock_balance': self.randrange(100, 1000, 1),
            'package_amount': self.randrange(1, 20, 2),
            'capacity_type': self.get_attr('Тип ёмкости:', product_initial, 'capacity_type', first_only=True),
        }

        sfacets = {
            'country': self.get_attr('Регион:', product_initial, 'country'),
            'type': self.get_attr('Пиво:', product_initial, 'type'),
            'style': self.get_attr('Стиль:', product_initial, 'style'),
            'brand': self.get_attr('Бренд:', product_initial, 'brand'),
            'fermentation': self.get_attr('Тип ферментации:', product_initial, 'fermentation'),
            'serving_temp': self.get_attr('Температура сервировки:', product_initial, 'serving_temp'),
            'composition': self.get_attr('Состав:', product_initial, 'composition'),
            'heat_treatment': self.get_attr('Тип термообработки:', product_initial, 'heat_treatment'),
            'kind': self.get_attr('Вид:', product_initial, 'kind'),
        }

        nfacets = {
            'strength': self.get_num_attr('Крепость:', product_initial, 'strength'),
            'density': self.get_num_attr('Плотность:', product_initial, 'density'),
        }

        if sfacets['composition'] is not None:
            composition_values = sfacets['composition']['values'][0]['name'].split(',')
            sfacets['composition']['values'] = [{'name': composition_value} for composition_value in composition_values]

        sfacets = {key: value for key, value in sfacets.items() if value is not None}
        nfacets = {key: value for key, value in nfacets.items() if value is not None}

        data['sfacets'] = sfacets
        data['nfacets'] = nfacets

        data['group_by'] = {
            'name': data['name'],
            'manufacturer': data['manufacturer'],
            **sfacets,
        }

        return data

    def get_attr(self, attr, product, code='', first_only=False, facet=True):
        try:
            row = [attrs for attrs in product['info'] if attrs['title'] == attr][0]
        except IndexError:
            return None

        value = row['value'][0] if first_only else [{'name': item} for item in row['value']]
        name = row['title'][:-1]
        return {
            'name': name,
            'values': value,
            'slug': code
        }

    def get_num_attr(self, attr, product, code=''):
        try:
            row = [attrs for attrs in product['info'] if attrs['title'] == attr][0]
        except IndexError:
            return None

        value = row['value'][0][:-1]
        value = int(float(value)) if int(float(value)) == float(value) else float(value)
        suffix = row['value'][0][-1]
        name = row['title'][:-1]
        return {
            'name': name,
            'value': value,
            'slug': code,
            'suffix': suffix
        }

    def get_products(self, path):
        products_path = "{root}/{path}".format(path=path, root=os.path.dirname(os.path.abspath(__file__)))
        with open(products_path) as products_file:
            products = json.load(products_file)
        return products

    def randrange(self, start, stop, step):
        return random.randint(0, int((stop - start) / step)) * step + start

    def create_product(self, products):
        product = products[0]
        product_data = {}

        manufacturer_model, created = Manufacturer.objects.get_or_create(name=product['manufacturer']['values'])

        product_data['name'] = product['name']
        product_data['manufacturer'] = manufacturer_model.pk
        product_data['category'] = product['category'].pk
        product_data['status'] = 'active'
        product_data['description'] = '"Hefeweizen Hell" от пивоварни Engel представляет собой традиционный баварский вайсбир, который изготавливается из ячменного (40%) и пшеничного (60%) солода, хмеля, выращенного в знаменитой области Халлертау, воды из собственного источника пивоварни и особого сорта дрожжей. Пиво производится по технологии дозревания в бутылке, благодаря чему имеет богатый и насыщенный вкус, отличающийся, тем не менее, свежестью и живостью характера.'

        tags = []
        for tag in product['tags']:
            tag_model, created = Tags.objects.get_or_create(name=tag)
            tags.append(tag_model.pk)
        product_data['tags'] = tags

        sfacets = self._create_sfacets(product['sfacets'])
        nfacets = self._create_nfacets(product['nfacets'])
        product_data['sfacets'] = sfacets
        product_data['nfacets'] = nfacets

        instances = []
        for product_instance in products:
            images = self._create_image(product_instance['image'])
            instance = {
                'sku': product_instance['sku'],
                'measure_count': product_instance['measure_count'],
                'measure_value': product_instance['measure_value'],
                'price': product_instance['price'],
                'stock_balance': product_instance['stock_balance'],
                'package_amount': product_instance['package_amount'],
                'images': images,
            }
            instances.append(instance)
        product_data['instances'] = instances

        serializer = ProductCreateSerializer(data=product_data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        elastic.index_product(instance)

    def _create_sfacets(self, facets):
        facet_ids = []
        for key, facet in facets.items():
            facet_model, created = SFacet.objects.get_or_create(name=facet['name'], slug=facet['slug'])

            for value in facet['values']:
                facet_values_model, created = SFacetValue.objects.get_or_create(name=value['name'], facet=facet_model)
                facet_ids.append(facet_values_model.pk)

        return facet_ids

    def _create_nfacets(self, facets):
        nfacets = []
        for key, facet in facets.items():
            facet_model, created = NFacet.objects.get_or_create(name=facet['name'], slug=facet['slug'], suffix=facet['suffix'])
            nfacets.append({'facet': facet_model.pk, 'value': facet['value']})

        return nfacets

    def _create_image(self, image):
        file_path = '{root}/all/images/beer/full/{filename}'.format(
            root=os.path.dirname(os.path.abspath(__file__)),
            filename=image
        )
        img_file = open(file_path, 'rb')
        image_model = ProductImage.objects.create(is_main=True)
        image_model.src.save(image, File(img_file))
        image_model.save()
        return [image_model.pk]





