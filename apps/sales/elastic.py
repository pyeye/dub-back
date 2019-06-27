import itertools
import json

from elasticsearch import Elasticsearch

from apps.products.models import ProductInstance

INDEX = 'products_dev'
CONFIG = {
    'host': 'elastic',
    'port': 9200,
    'http_auth': ('elastic', 'secret'),
    'timeout': 30,
    'max_retries': 10,
    'retry_on_timeout': True
}

PAGE_SIZE = 24

es = Elasticsearch([CONFIG])


def add_sale(sale_model):
    categories = format_categories(sale_model)
    products = format_products(sale_model)
    sale_products = get_sale_products(products)
    grouped_products = group_products_by_sale(products)
    categories_query = make_categories_query(categories, exclude_products=sale_products)
    products_query = make_products_query(grouped_products)
    queries = categories_query + products_query
    index_sale(queries)
    # db.add_category_sale(categories, exclude_products=sale_products)
    # to manager?
    for category in categories:
        instances = ProductInstance.objects.filter(
            product_info__category__slug=category['slug']
        ).exclude(pk__in=sale_products)
        for instance in instances:
            instance.sales.append(category['sale'])
            instance.save()
    # db.add_product_sale(grouped_products)
    # to manager?
    for group in grouped_products:
        instances = ProductInstance.objects.filter(pk__in=group['products'])
        for instance in instances:
            instance.sales.append(group['sale'])
            instance.save()


def remove_sale(sale_model):
    body = {
        "query": {
            "nested": {
                "path": "products",
                "query": {
                    "nested": {
                        "path": "products.sales",
                        "query": {
                            "bool": {
                                "filter": {
                                    "term": {"products.sales.pk": sale_model.pk}
                                }
                            }
                        }
                    }

                }
            }
        },
        "script": {
            "lang": "painless",
            "source": """
                for (int i = 0; i < ctx._source.products.length; ++i) {
                    for (int j = 0; j < ctx._source.products[i].sales.length; ++j) {
                        if (ctx._source.products[i].sales[j]['pk'] == params.sale) {
                            ctx._source.products[i].sales.remove(j);
                        }
                    }
                }
            """,
            "params": {
                "sale": sale_model.pk,
            }
        }
    }
    es.update_by_query(index=INDEX, body=body)

    instances = ProductInstance.objects.filter(sales__contains=[{'pk': sale_model.pk}])
    for instance in instances:
        instance.sales = [sale for sale in instance.sales if sale['pk'] != sale_model.pk]
        instance.save()


def update_sale(sale_model):
    remove_sale(sale_model)
    add_sale(sale_model)


def format_categories(sale_model):
    categories_dict = {}
    for category_set in sale_model.categorysale_set.all():
        sale = _get_sale_dict(sale_model)
        details = category_set.details if category_set.details else sale_model.details
        sale.update(details)
        categories_dict[category_set.category.slug] = sale

    return [{'slug': key, 'sale': values} for key, values in categories_dict.items()]


def format_products(sale_model):
    products_dict = {}
    for collection_set in sale_model.collectionsale_set.all():
        for collection_product in collection_set.collection.products.all():
            sale = _get_sale_dict(sale_model)
            details = collection_set.details if collection_set.details else sale_model.details
            sale.update(details)
            sale['hash'] = hash(json.dumps(details, sort_keys=True))
            products_dict[collection_product.pk] = sale

    for product_set in sale_model.productsale_set.all():
        sale = _get_sale_dict(sale_model)
        details = product_set.details if product_set.details else sale_model.details
        sale.update(details)
        sale['hash'] = hash(json.dumps(details, sort_keys=True))
        products_dict[product_set.product.pk] = sale

    return [{'pk': key, 'sale': values} for key, values in products_dict.items()]


def get_sale_products(products):
    return [product['pk'] for product in products]


def group_products_by_sale(products):
    sorted_products = sorted(products, key=lambda p: p['sale']['hash'])
    grouped_products = itertools.groupby(sorted_products, key=lambda p: p['sale']['hash'])
    sale_types = []
    for _, group in grouped_products:
        tmp_group = list(group)
        sale = tmp_group[0]['sale']
        sale.pop('hash', None)
        products = [item['pk'] for item in tmp_group]
        sale_types.append({'sale': sale, 'products': products})
    return sale_types


def make_categories_query(categories, exclude_products):
    query_bodies = []
    for category in categories:
        body = {
            "query": {
                "bool": {
                    "filter": {"term": {"category.slug": category['slug']}},
                }
            },
            "script": {
                "lang": "painless",
                "source": """
                        for (int i = 0; i < ctx._source.products.length; ++i) {
                            if (!params.exclude_products.contains(ctx._source.products[i]['pk'])) {
                                ctx._source.products[i].sales.add(params.sale);
                            }
                        }
                    """,
                "params": {
                    "exclude_products": exclude_products,
                    "sale": category['sale']
                }
            }
        }
        query_bodies.append(body)
    return query_bodies


def make_products_query(product_groups):
    query_bodies = []
    for sale_type in product_groups:
        body = {
            "query": {
                "bool": {
                    "filter": {
                        "nested": {
                            "path": "products",
                            "query": {"terms": {"products.pk": sale_type['products']}}
                        }
                    },
                }
            },
            "script": {
                "lang": "painless",
                "source": """
                    for (int i = 0; i < ctx._source.products.length; ++i) {
                        if (params.sale_products.contains(ctx._source.products[i]['pk'])) {
                            ctx._source.products[i].sales.add(params.sale);
                        }
                    }
                """,
                "params": {
                    "sale_products": sale_type['products'],
                    "sale": sale_type['sale']
                }
            }
        }
        query_bodies.append(body)
    return query_bodies


def index_sale(query_bodies):
    for query_body in query_bodies:
        es.update_by_query(index=INDEX, body=query_body, conflicts='proceed')


def _get_sale_dict(sale_model):
    return {
        'pk': sale_model.pk,
        'name': sale_model.name,
        'date_start': sale_model.date_start.isoformat(),
        'date_end': sale_model.date_end.isoformat(),
    }

