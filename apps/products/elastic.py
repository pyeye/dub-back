import itertools
import json
import datetime

from elasticsearch import Elasticsearch

from .serializers import ProductListSerializer
from .models import NFacet

INDEX = 'products_dev'
CONFIG = {
    'host': 'elastic',
    'port': 9200,
    'http_auth': ('elastic', 'secret')
}

PAGE_SIZE = 24

es = Elasticsearch([CONFIG])


def index_product(product_model):
    serializer = ProductListSerializer(product_model)
    data = json.loads(json.dumps(serializer.data))
    product_body = _create_product_body(data)
    es.index(index=INDEX, doc_type='_doc', body=product_body, id=data['pk'])


def delete_product(product_model):
    es.delete(index=INDEX, doc_type='_doc', id=product_model.pk)


def get_products(params):
    excludes = ['suggest', 'completion', 'fulltext_russian', 'fulltext_phonetic']
    return _elastic_get_products(params=params, excludes=excludes)


def add_collection(collection_model):
    product_ids = [prod.pk for prod in collection_model.products.all()]
    body = {
        "query": {
            "nested": {
                "path": "products",
                "query": {
                    "bool": {"filter": {"terms": {"products.pk": product_ids}}}
                }
            }
        },
        "script": {
            "lang": "painless",
            "source": """
                for (int i = 0; i < ctx._source.products.length; ++i) {
                    if (params.products.contains(ctx._source.products[i]['pk'])) {
                        ctx._source.products[i].collections.add(params.collection);
                    }
                }
            """,
            "params": {
                "collection": collection_model.pk,
                "products": product_ids
            }
        }
    }
    es.update_by_query(index=INDEX, body=body, conflicts='proceed')


def remove_collection(collection_model):
    body = {
        "query": {
            "nested": {
                "path": "products",
                "query": {
                    "bool": {"filter": {"term": {"products.collections": collection_model.pk}}}
                }
            }
        },
        "script": {
            "lang": "painless",
            "source": """
                for (int i = 0; i < ctx._source.products.length; ++i) {
                  int index = ctx._source.products[i].collections.indexOf(params.collection);
                  if (index >= 0) {
                    ctx._source.products[i].collections.remove(index);
                  }
                }
            """,
            "params": {
                "collection": collection_model.pk,
            }
        }
    }
    es.update_by_query(index=INDEX, body=body)


def update_collection(collection_model):
    remove_collection(collection_model)
    add_collection(collection_model)


def _elastic_get_products(params, excludes):
    filter_query = _create_filter_query(params)

    sort_param = params.get('sort', None)
    if sort_param is None:
        sort_query = [{'name': 'asc'}]
    else:
        sort_name, sort_type = sort_param.split('-')
        sort_query = {sort_name: sort_type}

    page = int(params.get('page', 1))
    page_from = 0 if page == 1 else PAGE_SIZE * (page - 1)

    query = {
        '_source': {
            'excludes': excludes
        },
        'query': {
            'bool': {
                'filter': filter_query
            }
        },
        'sort': sort_query,
        'from': page_from,
        'size': PAGE_SIZE,
    }

    products = es.search(index=INDEX, body=query)

    total_products = products['hits']['total']['value']

    formatted_products = []
    for product in products['hits']['hits']:
        source = product['_source']
        source['pk'] = product['_id']
        today = datetime.datetime.today()
        for instance in source['products']:
            price = float(instance['price'])
            instance['price'] = _format_price(price)
            if not instance['sales']:
                continue
            sales_with_fixed_price = []
            sales_with_percent_price = []
            new_price = price
            for sale in instance['sales']:
                date_start = datetime.datetime.strptime(sale['date_start'], '%Y-%m-%d')
                date_end = datetime.datetime.strptime(sale['date_end'], '%Y-%m-%d')
                if today < date_start or today > date_end:
                    continue
                if sale['type'] == 'fixed':
                    sales_with_fixed_price.append(sale['fixed'])
                if sale['type'] == 'percent':
                    sales_with_percent_price.append(sale['percent'])
            if sales_with_fixed_price:
                new_price = sales_with_fixed_price[-1]
            if sales_with_percent_price:
                percent = sales_with_percent_price[-1]
                new_price = new_price * ((100 - percent) / 100)
            if new_price != instance['price']:
                instance['new_price'] = _format_price(new_price)

        formatted_products.append(source)
    return {
        'items': formatted_products,
        'total': total_products,
    }


def get_product(pk):
    product = es.get(index=INDEX, doc_type='_doc', id=pk)
    source = product['_source']
    today = datetime.datetime.today()
    for instance in source['instances']:
        price = float(instance['price'])
        instance['price'] = _format_price(price)
        if not instance['sales']:
            continue
        sales_with_fixed_price = []
        sales_with_percent_price = []
        new_price = price
        for sale in instance['sales']:
            date_start = datetime.datetime.strptime(sale['date_start'], '%Y-%m-%d')
            date_end = datetime.datetime.strptime(sale['date_end'], '%Y-%m-%d')
            if today < date_start or today > date_end:
                continue
            if sale['type'] == 'fixed':
                sales_with_fixed_price.append(sale['fixed'])
            if sale['type'] == 'percent':
                sales_with_percent_price.append(sale['percent'])
        if sales_with_fixed_price:
            new_price = sales_with_fixed_price[-1]
        if sales_with_percent_price:
            percent = sales_with_percent_price[-1]
            new_price = new_price * ((100 - percent) / 100)
        if new_price != instance['price']:
            instance['new_price'] = _format_price(new_price)
    return source


def get_tags(category):
    query = {
        "size": 0,
        "aggs": {
            "category_tags": {
                "filter": {"term": {"category.slug": category}},
                "aggs": {
                    "nested_tags": {
                        "nested": {
                            "path": "tags"
                        },
                        "aggs": {
                            "tags": {
                                "terms": {
                                    "field": "tags.name"
                                },
                                "aggs": {
                                    "tags_src": {
                                        "top_hits": {
                                            "size": 1,
                                            "_source": {"includes": ["tags"]}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    tags = es.search(index=INDEX, body=query)
    formatted_tags = []
    for tag in tags['aggregations']['category_tags']['nested_tags']['tags']['buckets']:
        formatted_tags.append(tag['tags_src']['hits']['hits'][0]['_source'])
    return formatted_tags


def get_categories():
    query = {
        "size": 0,
        "aggs": {
            "category": {
                "terms": {
                    "field": "category.name"
                },
                "aggs": {
                    "category_src": {
                        "top_hits": {
                            "size": 1,
                            "sort": [{"created_at": {"order": "desc"}}],
                            "_source": {"includes": ["name", "products", "category"]}
                        }
                    }
                }
            }
        }
    }
    elastic_categories = es.search(index=INDEX, body=query)
    categories = []
    for category in elastic_categories['aggregations']['category']['buckets']:
        categories.append({'pk': category['category_src']['hits']['hits'][0]['_id'], **category['category_src']['hits']['hits'][0]['_source']})

    return categories


def get_facets(params):
    filter_query = _create_filter_query(params)
    query = {
        "aggs": {
            "string_facets_filter": {
                'filter': {
                    "bool": {
                        "filter": filter_query
                    }
                },
                "aggs": {
                    "string_facets": {
                        "nested": {"path": "string_facets"},
                        "aggs": {
                            "facets_code": {
                                "terms": {
                                    "field": "string_facets.slug",
                                    "order": {
                                        "_key": "asc"
                                    }
                                },
                                "aggs": {
                                    "facets_src": {
                                        "top_hits": {
                                            "size": 1,
                                            "_source": {"includes": ["string_facets.slug", "string_facets.name"]}
                                        }
                                    },
                                    "facets_nested": {
                                        "nested": {"path": "string_facets.values"},
                                        "aggs": {
                                            "facet_values": {
                                                "terms": {
                                                    "field": "string_facets.values.pk",
                                                    "order": {
                                                        "_key": "asc"
                                                    }
                                                },
                                                "aggs": {
                                                    "facet_values_src": {
                                                        "top_hits": {
                                                            "size": 1,
                                                            "_source": {"includes": ["string_facets.values.pk",
                                                                                     "string_facets.values.name"]}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "number_facets": {
                "nested": {"path": "number_facets"},
                "aggs": {
                    "facets_code": {
                        "terms": {
                            "field": "number_facets.slug",
                            "order": {
                                "_key": "asc"
                            }
                        },
                        "aggs": {
                            "facets_src": {
                                "top_hits": {
                                    "size": 1,
                                    "_source": {"includes": ["number_facets"]}
                                }
                            },
                            "facets_stats": {
                                "stats": {
                                    "field": "number_facets.value"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    all_facets = es.search(index=INDEX, body=query)

    string_facets = []
    for string_facet_aggs in all_facets['aggregations']['string_facets_filter']['string_facets']['facets_code']['buckets']:
        facet_key = string_facet_aggs['key']
        facet_name = string_facet_aggs['facets_src']['hits']['hits'][0]['_source']['name']
        string_facet_items = []
        for facet_item in string_facet_aggs['facets_nested']['facet_values']['buckets']:
            string_facet_obj = facet_item['facet_values_src']['hits']['hits'][0]['_source']
            string_facet_obj['count'] = facet_item['doc_count']
            string_facet_items.append(string_facet_obj)
        string_facets_obj = {
            'slug': facet_key,
            'values': string_facet_items,
            'name': facet_name
        }
        string_facets.append(string_facets_obj)

    sfilters = params.getlist('sfacets[]')
    if len(sfilters)> 1:
        category = params.get('category')
        for sfilter in sfilters:
            attribute, values = sfilter.split(':')
            special_agg_query = _create_special_aggs(category, attribute, sfilters)
            special_aggs = es.search(body=special_agg_query)
            sp_string_facet_items = []
            for bucket in special_aggs['aggregations']['special_agg']['nested_agg']['string_facets_agg']['nested_values']['facets_values']['buckets']:
                sp_string_facets_obj = bucket['values_src']['hits']['hits'][0]['_source']
                sp_string_facets_obj['count'] = bucket['doc_count']
                sp_string_facet_items.append(sp_string_facets_obj)
            facet_index = next((index for (index, d) in enumerate(string_facets) if d['slug'] == attribute), None)
            if facet_index is not None:
                string_facets[facet_index]['values'] = sp_string_facet_items

    number_facets = []
    for number_facet_aggs in all_facets['aggregations']['number_facets']['facets_code']['buckets']:
        source = number_facet_aggs['facets_src']['hits']['hits'][0]['_source']
        stats = number_facet_aggs['facets_stats']
        number_facets_obj = {
            'slug': source['slug'],
            'name': source['name'],
            'suffix': source['suffix'],
            'stats': {
                'min': stats['min'],
                'max': stats['max'],
            },

        }
        number_facets.append(number_facets_obj)

    return string_facets, number_facets


def _create_product_body(product):
    sfacets = []
    tmp_sfacets = product['sfacets']
    tmp_sfacets.sort(key=lambda elem: elem['facet']['pk'])
    groups = itertools.groupby(tmp_sfacets, lambda elem: elem['facet'])

    for facet, values in groups:
        # При удалении параметра is_active у оригинального словаря facet нарушается группировка
        tmp_facet = dict(facet)
        tmp_facet.pop('is_active', None)
        tmp_facet['values'] = [{'pk': value['pk'], 'name': value['name']} for value in values]
        sfacets.append(tmp_facet)

    tags = [{'pk': tag['pk'], 'name': tag['name']} for tag in product['tags']]

    nfacets = []
    for nfacet in product['nfacets']:
        nfacet_model = NFacet.objects.get(pk=nfacet['facet'])
        nfacets.append({
            'pk': nfacet_model.pk,
            'slug': nfacet_model.slug,
            'name': nfacet_model.name,
            'suffix': nfacet_model.suffix,
            'value': nfacet['value'],
        })


    body = {
        'name': product['name'],
        'manufacturer': {
            'name': product['manufacturer']['name'],
            'slug': product['manufacturer']['slug'],
            'pk': product['manufacturer']['pk'],
        },
        'category': {
            'name': product['category']['name'],
            'slug': product['category']['slug'],
            'pk': product['category']['pk'],
        },
        'description': product['description'],
        'tags': tags,
        'products': product['instances'],
        'string_facets': sfacets,
        'number_facets': nfacets,
        'created_at': product['created_at']
    }

    return body

def _create_filter_query(params):
    filter_query = []

    category = params.get('category', None)
    if category is not None:
        category_query = {'term': {'category.slug': category}}
        filter_query.append(category_query)

    tags_params = params.get('tags', None)
    if tags_params is not None:
        tags_query = []
        tags = tags_params.split(',')
        for tag in tags:
            tag_query = {
                "nested": {
                    "path": "tags",
                    "query": {
                        "bool": {"filter": {"term": {"tags.pk": int(tag)}}}
                    }
                }
            }
            tags_query.append(tag_query)
        filter_query.append(tags_query)

    sales_param = params.get('sales', None)
    if sales_param is not None:
        sales_query = []
        sales = sales_param.split(',')
        for sale in sales:
            sale_query = {
                "nested": {
                    "path": "products",
                    "query": {
                        "nested": {
                            "path": "products.sales",
                            "query": {
                                "bool": {
                                    "filter": {
                                        "term": {"products.sales.pk": int(sale)}
                                    }
                                }
                            }
                        }

                    }
                }
            }
            sales_query.append(sale_query)
        filter_query.append(sales_query)

    string_facets_params = params.getlist('sfacets[]')
    if string_facets_params:
        sfacet_query = []
        for string_facets_param in string_facets_params:
            attribute, values = string_facets_param.split(':')
            values = values.split(',')
            facet = {
                "nested": {
                    "path": "string_facets",
                    "query": {
                        "bool": {
                            "filter": [
                                {"term": {"string_facets.slug": attribute}},
                                {
                                    "nested": {
                                        "path": "string_facets.values",
                                        "query": {
                                            "terms": {"string_facets.values.pk": values}
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
            sfacet_query.append(facet)
        filter_query += sfacet_query

    number_facets_params = params.getlist('nfacets[]')
    if number_facets_params:
        nfacet_query = []
        for number_facets_param in number_facets_params:
            attribute, values = number_facets_param.split(':')
            min_val, max_val = [_get_number(value) for value in values.split('-')]
            facet = {
              "nested": {
                "path": "number_facets",
                "query": {
                  "bool": {
                    "filter": [
                      {"term": {"number_facets.slug": attribute}},
                      {
                        "range" : {
                          "number_facets.value" : {
                              "gte" : min_val,
                              "lte" : max_val
                          }
                        }
                      }
                    ]
                  }
                }
              }
            }
            nfacet_query.append(facet)
        filter_query += nfacet_query

    return filter_query

def _create_special_aggs(category, attribute, sfilters):
    special_aggs_query = []
    for sfilter in sfilters:
        special_attr, values = sfilter.split(':')
        if special_attr == attribute:
            continue
        values = values.split(',')
        special_agg_query = {"nested": {
                  "path": "string_facets",
                  "query": {
                    "bool": {
                      "filter": [
                        {"term": {"string_facets.slug": {"value": special_attr}}},
                        {"nested": {
                          "path": "string_facets.values",
                          "query": {"terms": {"string_facets.values.pk": values}}
                        }}
                      ]
                    }
                  }
                }}
        special_aggs_query.append(special_agg_query)

    filter_query = []
    category_query = {"term": {"category.slug": category}}
    filter_query.append(category_query)
    filter_query += special_aggs_query
    query = {
      "size": 0,
      "aggs": {
        "special_agg": {
          "filter": {
            "bool": {
              "filter": filter_query
            }
          },
          "aggs": {
            "nested_agg": {
              "nested": {
                "path": "string_facets"
              },
              "aggs": {
                  "string_facets_agg": {
                    "filter": {"term": {"string_facets.slug": attribute}},
                    "aggs": {
                      "nested_values": {
                        "nested": {
                          "path": "string_facets.values"
                        },
                        "aggs": {
                            "facets_values": {
                              "terms": {
                                  "field": "string_facets.values.pk"
                              },
                              "aggs": {
                                "values_src": {
                                  "top_hits": {
                                    "size": 1,
                                    "_source": { "includes": ["string_facets.values.pk", "string_facets.values.name"]}
                                  }
                                }
                              }
                            }
                          }
                      }
                    }
                  }
                }
            }
          }
        }
      }
    }
    return query

def _get_number(str_value):
    try:
        return int(str_value)
    except ValueError:
        return float(str_value)


def update_category(category):
    body = {
        "query": {"term": {"category.pk": category['pk']}},
        "script": {
            "source": "ctx._source.category = params.category",
            "lang": "painless",
            "params": {
                "category": category
            }
        }
    }
    es.update_by_query(index=INDEX, body=body)


def delete_category(category):
    body = {"query": {"term": {"category.pk": category['pk']}}}
    es.delete_by_query(index=INDEX, body=body)


def update_manufacturer(manufacturer):
    body = {
        "query": {"term": {"manufacturer.pk": manufacturer['pk']}},
        "script": {
            "source": "ctx._source.manufacturer = params.manufacturer",
            "lang": "painless",
            "params": {
                "manufacturer": manufacturer
            }
        }
    }
    es.update_by_query(index=INDEX, body=body)


def delete_manufacturer(manufacturer):
    body = {"query": {"term": {"manufacturer.pk": manufacturer['pk']}}}
    es.delete_by_query(index=INDEX, body=body)


def update_tag(tag):
    body = {
      "query": {
        "nested": {
          "path": "tags",
          "query": {
            "bool": {"filter": {"term": {"tags.pk": tag['pk']}}}
          }
        }
      },
      "script": {
        "lang": "painless",
        "source": """
            for (int i = 0; i < ctx._source.tags.length; ++i) {
                if (ctx._source.tags[i]['pk'] == params.tag['pk']) {
                    ctx._source.tags[i] = params.tag;
                }
            }
        """,
        "params": {
          "tag": tag
        }
      }
    }
    es.update_by_query(index=INDEX, body=body)


def delete_tag(tag):
    body = {
      "query": {
        "nested": {
          "path": "tags",
          "query": {
            "bool": {"filter": {"term": {"tags.pk": tag['pk']}}}
          }
        }
      },
      "script": {
        "lang": "painless",
        "source": """
            ctx._source.tags.remove(ctx._source.tags.indexOf(params.tag))
        """,
        "params": {
          "tag": tag
        }
      }
    }
    es.update_by_query(index=INDEX, body=body)


def update_sfacet(string_facet):
    body = {
      "query": {
        "nested": {
          "path": "string_facets",
          "query": {
            "bool": {"filter": {"term": {"string_facets.pk": string_facet['pk']}}}
          }
        }
      },
      "script": {
        "lang": "painless",
        "source": """
            for (int i = 0; i < ctx._source.string_facets.length; ++i) {
                if (ctx._source.string_facets[i]['pk'] == params.string_facet['pk']) {
                    ctx._source.string_facets[i]['name'] = params.string_facet['name'];
                    ctx._source.string_facets[i]['slug'] = params.string_facet['slug'];
                }
            }
        """,
        "params": {
          "string_facet": string_facet
        }
      }
    }
    es.update_by_query(index=INDEX, body=body)


def delete_sfacet(pk):
    body = {
        "query": {
            "nested": {
                "path": "string_facets",
                "query": {
                    "bool": {"filter": {"term": {"string_facets.pk": pk}}}
                }
            }
        },
        "script": {
            "lang": "painless",
            "source": """
                for (int i = 0; i < ctx._source.string_facets.length; ++i) {
                    if (ctx._source.string_facets[i]['pk'] == params.pk) {
                        ctx._source.string_facets.remove(i)
                    }
                }
            """,
            "params": {
                "pk": pk
            }
        }
    }
    es.update_by_query(index=INDEX, body=body)


def update_sfacet_value(value):
    body = {
        "query": {
            "nested": {
                "path": "string_facets",
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"string_facets.pk": value['facet_pk']}},
                            {
                                "nested": {
                                    "path": "string_facets.values",
                                    "query": {
                                        "term": {"string_facets.values.pk": value['pk']}
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        },
        "script": {
            "lang": "painless",
            "source": """
                for (int i = 0; i < ctx._source.string_facets.length; ++i) {
                    if (ctx._source.string_facets[i]['pk'] == params.value['facet']['pk']) {
                        for (int j = 0; j < ctx._source.string_facets[i].values.length; ++j) {
                            if (ctx._source.string_facets[i].values[j]['pk'] == params.value['pk']) {
                                ctx._source.string_facets[i].values[j]['name'] = params.value['name'];
                            }
                        }
                    }
                }
            """,
            "params": {
                "value": value
            }
        }
    }
    es.update_by_query(index=INDEX, body=body)


def delete_sfacet_value(value):
    body = {
        "query": {
            "nested": {
                "path": "string_facets",
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"string_facets.pk": value['facet']['pk']}},
                            {
                                "nested": {
                                    "path": "string_facets.values",
                                    "query": {
                                        "term": {"string_facets.values.pk": value['pk']}
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        },
        "script": {
            "lang": "painless",
            "source": """
                for (int i = 0; i < ctx._source.string_facets.length; ++i) {
                    if (ctx._source.string_facets[i]['pk'] == params.value['facet']['pk']) {
                        for (int j = 0; j < ctx._source.string_facets[i].values.length; ++j) {
                            if (ctx._source.string_facets[i].values[j]['pk'] == params.value['pk']) {
                                ctx._source.string_facets[i].values.remove(j)
                            }
                        }
                    }
                }
            """,
            "params": {
                "value": value
            }
        }
    }
    es.update_by_query(index=INDEX, body=body)


def update_nfacet(facet):
    body = {
      "query": {
        "nested": {
          "path": "number_facets",
          "query": {
            "bool": {"filter": {"term": {"number_facets.pk": facet['pk']}}}
          }
        }
      },
      "script": {
        "lang": "painless",
        "source": """
            for (int i = 0; i < ctx._source.number_facets.length; ++i) {
                if (ctx._source.number_facets[i]['pk'] == params.facet['pk']) {
                    ctx._source.number_facets[i]['name'] = params.facet['name'];
                    ctx._source.number_facets[i]['slug'] = params.facet['slug'];
                }
            }
        """,
        "params": {
          "facet": facet
        }
      }
    }
    es.update_by_query(index=INDEX, body=body)


def delete_nfacet(pk):
    body = {
        "query": {
            "nested": {
                "path": "number_facets",
                "query": {
                    "bool": {"filter": {"term": {"number_facets.pk": pk}}}
                }
            }
        },
        "script": {
            "lang": "painless",
            "source": """
                for (int i = 0; i < ctx._source.number_facets.length; ++i) {
                    if (ctx._source.number_facets[i]['pk'] == params.pk) {
                        ctx._source.number_facets.remove(i)
                    }
                }
            """,
            "params": {
                "pk": pk
            }
        }
    }
    es.update_by_query(index=INDEX, body=body)


def _format_price(price):
    return str(int(price)) if price % 1 == 0 else "{:.2f}".format(price)
