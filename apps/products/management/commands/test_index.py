import os
import json
import random

from django.core.management.base import BaseCommand
from django.core.files import File
from apps.products.models import ProductInfo, ProductInstance, Manufacturer, Category, Attribute, AttributeValue
from apps.products.elastic import create_product_document


class Command(BaseCommand):

    def handle(self, *args, **options):
        products = self.get_products('winestyle/result.json')
        for index, product_initial in enumerate(products):
            product_data = self.get_product_data(product_initial)
            product_data['sku'] = index
            product_model = self.create_product_model(product_data)
            create_product_document(product_model, product_data)

    def get_product_data(self, product_initial):
        country = self.get_attr('Регион:', product_initial, 'country')
        type = self.get_attr('Пиво:', product_initial, 'type')
        style = self.get_attr('Стиль:', product_initial, 'style')
        manufacturer = self.get_attr('Производитель:', product_initial, 'manufacturer', first_only=True)
        brand = self.get_attr('Бренд:', product_initial, 'brand')
        measure = self.get_attr('Объем:', product_initial, 'measure', first_only=True)
        measure_count, measure_value = measure['values'].split()
        strength = self.get_num_attr('Крепость:', product_initial, 'strength')
        category = Category.objects.get(slug='beer')
        name = product_initial['title'].split(',')[0].split(maxsplit=1)[1]
        tags = [{'name': item} for item in product_initial['tags']]
        image = product_initial['images'][0]['path'].split('/')[1]
        is_active = True
        price = self.randrange(200, 1000, 50)
        stock_balance = self.randrange(100, 1000, 1)
        package_amount = self.randrange(1, 20, 2)


        all_vars = vars()
        del all_vars['product_initial']
        del all_vars['self']
        if all_vars['brand'] is None:
            del all_vars['brand']
        return all_vars

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

    def create_product_model(self, product):
        try:
            manufacturer = Manufacturer.objects.get(name=product['manufacturer']['values'])
        except Manufacturer.DoesNotExist:
            manufacturer = Manufacturer.objects.create(name=product['manufacturer']['values'])



        string_facets = [
            product['country'],
            product['type'],
            product['style'],
        ]

        brand = product.get('brand', None)
        if brand is not None:
            string_facets.append(brand)

        price_facet = {
            'name': 'Цена',
            'slug': 'price',
            'value': product['price'],
            'suffix': '\u20BD'
        }

        number_facets = [
            product['strength'],
            price_facet,
        ]

        string_facets = self._create_facets_attributes(string_facets)
        product['tags'] = self._create_tags_attributes(product['tags'])

        manufacturer_facet = {
            'name': 'Производитель',
            'slug': 'manufacturer',
            'values': [{'name': manufacturer.name, 'code': manufacturer.pk}]
        }

        string_facets.append(manufacturer_facet)

        product_info = ProductInfo.objects.create(
            name=product['name'],
            manufacturer=manufacturer,
            category=product['category'],
            string_facets=string_facets,
            number_facets=number_facets,
            tags=product['tags']
        )

        product_instance = ProductInstance(
            sku=product['sku'],
            is_active=product['is_active'],
            product_info=product_info,
            measure_count=product['measure_count'],
            measure_value=product['measure_value'],
            price=product['price'],
            stock_balance=product['stock_balance'],
            package_amount=product['package_amount']
        )

        filename = product['image']
        file_path = '{root}/winestyle/images/beer/{filename}'.format(
            root=os.path.dirname(os.path.abspath(__file__)),
            filename=filename
        )
        img_file = open(file_path, 'rb')
        product_instance.image.save(filename, File(img_file))
        product_instance.save()

        return product_instance

    def _create_facets_attributes(self, facets):
        for facet in facets:
            try:
                attribute = Attribute.objects.get(slug=facet['slug'])
            except Attribute.DoesNotExist:
                attribute = Attribute.objects.create(name=facet['name'], slug=facet['slug'])

            for value in facet['values']:
                try:
                    attribute_value = AttributeValue.objects.get(name=value['name'], attribute_id=attribute.pk)
                except AttributeValue.DoesNotExist:
                    attribute_value = AttributeValue.objects.create(name=value['name'], attribute=attribute)

                value['code'] = attribute_value.pk

        return facets

    def _create_tags_attributes(self, tags):
        try:
            attribute = Attribute.objects.get(slug='tags')
        except Attribute.DoesNotExist:
            attribute = Attribute.objects.create(name='Метки', slug='tags')
        for tag in tags:
            try:
                attribute_value = AttributeValue.objects.get(name=tag['name'], attribute_id=attribute.pk)
            except AttributeValue.DoesNotExist:
                attribute_value = AttributeValue.objects.create(name=tag['name'], attribute=attribute)

            tag['code'] = attribute_value.pk

        return tags





