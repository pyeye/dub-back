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
    NFacetValue,
    ProductImage,
)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        all_products = self.get_products('all_products/rusbeer/import.json')
        products_data = list()
        for product in all_products:
            print(product)
            try:
                initial_data = self.get_product_data(product)
            except NoImageException:
                continue
            products_data.append(initial_data)
        grouped_products = itertools.groupby(products_data, lambda elem: elem['name'])
        for index, (group_by, product) in enumerate(grouped_products):
            tmp_prods = list(product)
            print('go-{0} | len-{1}'.format(index, len(tmp_prods)))
            self.create_product(tmp_prods)
  
    def get_products(self, path):
        products_path = "{root}/{path}".format(path=path, root=os.path.dirname(os.path.abspath(__file__)))
        with open(products_path) as products_file:
            products = json.load(products_file)
        return products

    
    def get_product_data(self, product_initial):
        if not product_initial['files']:
            raise NoImageException
        data = {
            'sku': randint(0, 10000000),
            'name': product_initial['name'],
            'description': product_initial['description'],
            'category': Category.objects.get(slug='beer'),
            'manufacturer': product_initial['brand'] if product_initial['brand'] is not None else 'Нет данных',
            'measure': self.format_measure(product_initial['measure']),
            'image': product_initial['files'][0]['path'].split('/')[1],
            'base_price': self.randrange(200, 1000, 50),
            'stock_balance': self.randrange(100, 1000, 1),
            'package_amount': self.randrange(1, 20, 2),
            'extra': {
                'name_locale': product_initial['name_locale'],
                'style_locale': product_initial['style_locale']
            }
        }

        sfacets = {
            'country': self.get_attr('Регион', product_initial, 'country', first_only=True),
            'type': self.get_attr('Тип', product_initial, 'type'),
            'style': self.get_attr('Стиль', product_initial, 'style', first_only=True),
            'brand': self.get_attr('Бренд', product_initial, 'brand', first_only=True),
            'color': self.get_attr('Цвет', product_initial, 'color'),
            'foam': self.get_attr('Пена', product_initial, 'foam'),
            'composition': self.get_attr('Состав', product_initial, 'composition'),
            'taste': self.get_attr('Вкус', product_initial, 'taste'),
            'after_taste': self.get_attr('Послевкусие', product_initial, 'after_taste'),
        }

        nfacets = {
            'strength': self.get_num_attr('Крепость', product_initial, 'strength', suffix='%'),
            'density': self.get_num_attr('Плотность', product_initial, 'density', suffix='%'),
            'ibu': self.get_num_attr('IBU', product_initial, 'ibu'),
        }

        

        sfacets = {key: value for key, value in sfacets.items() if value is not None}
        nfacets = {key: value for key, value in nfacets.items() if value is not None}

        data['sfacets'] = sfacets
        data['nfacets'] = nfacets

        

        try:
            values = [value['name'] for value in sfacets['brand']['values']]
            values.sort()
            group_brand = ''.join(values)
        except KeyError:
            group_brand = ''
        
        try:
            values = [value['name'] for value in sfacets['type']['values']]
            values.sort()
            group_type = ''.join(values)
        except KeyError:
            group_type = ''
        
        try:
            values = [value['name'] for value in sfacets['country']['values']]
            values.sort()
            group_country = ''.join(values)
        except KeyError:
            group_country = ''

        try:
            values = [value['name'] for value in sfacets['composition']['values']]
            values.sort()
            group_composition = ''.join(values)
        except KeyError:
            group_composition = ''

        group_by = {
            'name': data['name'],
            'brand': group_brand,
            'type': group_type,
            'country': group_country,
            'composition': group_composition,
        }
        group_hash = hash(json.dumps(group_by, sort_keys=True))
        data['group_by'] = group_hash

        return data
    

    def get_attr(self, attr, product, code='', first_only=False, facet=True):
        try:
            if product[code] is None:
                return None
        except KeyError:
            return None

        value = [{'name': product[code].strip()}] if first_only else [{'name': item.strip()} for item in product[code]]
        return {
            'name': attr,
            'values': value,
            'slug': code
        }
    
    def get_num_attr(self, attr, product, code='', suffix=''):
        try:
            if product[code] is None or product[code] == '' or product[code] == '-':
                return None
        except KeyError:
            return None
        
        value = product[code].replace(',', '.')
        value = int(float(value)) if int(float(value)) == float(value) else float(value)
        return {
            'name': attr,
            'value': value,
            'slug': code,
            'suffix': suffix
        }
    
    def format_measure(self, measure):
        try:
            count = int(measure)
        except ValueError:
            count = float(measure)
        return int(count * 1000)
    

    def create_product(self, products):
        product = products[0]
        product_data = {}

        manufacturer_model, created = Manufacturer.objects.get_or_create(name=product['manufacturer'])

        product_data['name'] = product['name']
        product_data['manufacturer'] = manufacturer_model.pk
        product_data['category'] = product['category'].pk
        product_data['status'] = 'active'
        product_data['tags'] = []
        product_data['extra'] = product['extra']

        product['description'] = '' if product['description'] == '.' else product['description'] 
        product_data['description'] = product['description']



        sfacets = self._create_sfacets(product['sfacets'])
        nfacets = self._create_nfacets(product['nfacets'])
        product_data['sfacets'] = sfacets
        product_data['nfacets'] = nfacets

        instances = []
        for product_instance in products:
            images = self._create_image(product_instance['image'])
            instance = {
                'sku': product_instance['sku'],
                'measure': product_instance['measure'],
                'status': 'active',
                'base_price': product_instance['base_price'],
                'stock_balance': product_instance['stock_balance'],
                'package_amount': product_instance['package_amount'],
                'images': images,
            }
            instances.append(instance)
        product_data['instances'] = instances

        serializer = ProductCreateSerializer(data=product_data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        elastic.index_products(instance)
    

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
            facet_value_model = NFacetValue.objects.create(value=facet['value'], facet=facet_model)
            nfacets.append(facet_value_model.pk)

        return nfacets
    

    def _create_image(self, image):
        file_path = '{root}/all_products/rusbeer/files/full/{filename}'.format(
            root=os.path.dirname(os.path.abspath(__file__)),
            filename=image
        )
        img_file = open(file_path, 'rb')
        image_model = ProductImage.objects.create(is_main=True)
        image_model.src.save(image, File(img_file))
        image_model.save()
        return [image_model.pk]

    def randrange(self, start, stop, step):
        return random.randint(0, int((stop - start) / step)) * step + start


class NoImageException(Exception):
    pass
    
