from elasticsearch.helpers import bulk

from apps.base.elastic import es, INDEX
from apps.products.models import ProductInstance

def add_sale(product_instances):
    query_bodies = _make_products_query(op_type='update', products=product_instances)
    bulk(es, query_bodies)

def delete_sale(product_instances):
    query_bodies = _make_products_query(op_type='update', products=product_instances)
    bulk(es, query_bodies)

def update_sale(product_instances):
    delete_sale(product_instances)
    add_sale(product_instances)


def _make_products_query(op_type, products):
    queries = []
    for product in products:
        script = _make_script(product)
        body = {
            '_op_type': op_type,
            '_index': INDEX,
            '_type': '_doc',
            '_id': product['instance_pk'],
            'script': script
        }
        queries.append(body)
    return queries

def _make_script(product):
    source = """
        ctx._source.instance.sales = params.sales;
        ctx._source.instance.price = params.price;
    """
    params = {
        'instance_pk': product['instance_pk'],
        'sales': product['sales'],
        'price': product['price'],
    }
    return { "source": source, "params" : params, "lang" : "painless" }