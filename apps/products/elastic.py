import itertools
import json
import datetime
from decimal import Decimal

from elasticsearch import Elasticsearch, helpers, exceptions
from django.conf import settings

from .serializers import ProductListSerializer, ProductInstanceSerializer
from .models import NFacet, ProductInstance


es = Elasticsearch([settings.ELASTIC_SEARCH["CONFIG"]])
EXCLUDED_FIELDS = ["suggest", "completion", "fulltext_russian", "fulltext_phonetic"]


def index_products(product_model):
    serializer = ProductListSerializer(product_model)
    data = json.loads(json.dumps(serializer.data))
    product_info_source = _create_product_info_source(data)
    actions = []
    count_instances = len(data["instances"])
    for product_instance in data["instances"]:
        # TODO: if в цикле - плохо. сделать цикл по уже фильтрованным инстансам
        if product_instance["status"] != ProductInstance.STATUS_ACTIVE:
            continue
        source = {
            **product_info_source,
            "count_instances": count_instances,
            "instance": product_instance,
        }
        actions.append(
            {
                "_index": settings.ELASTIC_SEARCH["INDEX"],
                "_id": product_instance["pk"],
                "_type": "_doc",
                "_op_type": "create",
                "_source": source,
            }
        )

    if actions:
        helpers.bulk(es, actions)


def index_product_instance(product_info, product_instance):
    if product_instance.status != ProductInstance.STATUS_ACTIVE:
        es.delete(index=settings.ELASTIC_SEARCH['INDEX'], doc_type='_doc', id=product_instance.pk)
        return
    info_serializer = ProductListSerializer(product_info)
    info_data = json.loads(json.dumps(info_serializer.data))

    instance_serializer = ProductInstanceSerializer(product_instance)
    instance_data = json.loads(json.dumps(instance_serializer.data))

    product_info_source = _create_product_info_source(info_data)
    source = {
        **product_info_source,
        'instance': instance_data,
    }
    es.index(index=settings.ELASTIC_SEARCH['INDEX'], body=source, doc_type='_doc', id=instance_data['pk'])


def delete_product(product_model):
    es.delete(index=settings.ELASTIC_SEARCH['INDEX'], doc_type='_doc', id=product_model.id)


def add_collection(collection_model):
    product_ids = list(collection_model.products.values_list("pk", flat=True))
    body = {
        "query": {"bool": {"filter": {"terms": {"instance.pk": product_ids}}}},
        "script": {
            "lang": "painless",
            "source": """
                ctx._source.instance.collections.add(params.collection);
            """,
            "params": {
                "collection": collection_model.pk,
            },
        },
    }
    es.update_by_query(
        index=settings.ELASTIC_SEARCH["INDEX"], body=body, conflicts="proceed"
    )


def remove_collection(collection_model):
    body = {
        "query": {
            "bool": {"filter": {"term": {"instance.collections": collection_model.pk}}}
        },
        "script": {
            "lang": "painless",
            "source": """
                int index = ctx._source.instance.collections.indexOf(params.collection);
                if (index >= 0) {
                    ctx._source.instance.collections.remove(index);
                }
            """,
            "params": {
                "collection": collection_model.pk,
            },
        },
    }
    es.update_by_query(index=settings.ELASTIC_SEARCH["INDEX"], body=body)


def update_collection(collection_model):
    remove_collection(collection_model)
    add_collection(collection_model)


def get_products(params):
    filter_query = _create_filter_query(params)

    sort_name, sort_type = params.get("sort")
    sort_query = {sort_name: sort_type}

    page = params.get("page")
    page_from = settings.ELASTIC_SEARCH["PAGE_SIZE"] * (page - 1)

    query = {
        "_source": {"excludes": EXCLUDED_FIELDS},
        "query": {"bool": {"filter": filter_query}},
        "sort": sort_query,
        "from": page_from,
        "size": settings.ELASTIC_SEARCH["PAGE_SIZE"],
    }

    products = es.search(index=settings.ELASTIC_SEARCH["INDEX"], body=query)

    total_products = products["hits"]["total"]["value"]
    formatted_products = []

    for hit in products["hits"]["hits"]:
        product = _format_product(hit['_source'])
        product["pk"] = hit["_id"]
        formatted_products.append(product)

    return {
        "items": formatted_products,
        "total": total_products,
    }


def get_product_info(pk):
    query = {
        "_source": {"excludes": EXCLUDED_FIELDS},
        "query": {
            "term": {"product_info_pk": str(pk)},
        },
    }

    products = es.search(index=settings.ELASTIC_SEARCH["INDEX"], body=query)
    hits = products["hits"]["hits"]

    if not hits:
        return None

    product_info = hits[0]["_source"]
    product_info['instances'] = []
    for nfacet in product_info['number_facets']:
        nfacet["value"] = _format_number(nfacet["value"])
    for product in hits:
        instance = product["_source"]['instance']
        instance['price'] = _format_number(instance['price'])
        instance['base_price'] = _format_number(instance['base_price'])
        product_info['instances'].append(instance)

    product_info.pop("instance", None)

    return product_info


def get_product_instance(pk):
    try:
        product = es.get(index=settings.ELASTIC_SEARCH["INDEX"], doc_type="_doc", id=pk)
    except exceptions.NotFoundError:
        return None

    for exclude_field in EXCLUDED_FIELDS:
        product["_source"].pop(exclude_field, None)
    formatted_product = _format_product(product["_source"])

    return formatted_product


def _format_product(product):
    product['instance']['price'] = _format_number(product['instance']['price'])
    product['instance']['base_price'] = _format_number(product['instance']['base_price'])
    for nfacet in product["number_facets"]:
        nfacet["value"] = _format_number(nfacet["value"])
    return product


def get_tags(params):
    filter_query = _create_filter_query(params)
    query = {
        "size": 0,
        "aggs": {
            "category_tags": {
                "filter": {
                    "bool": {
                        "filter": filter_query
                    }
                },
                "aggs": {
                    "nested_tags": {
                        "nested": {
                            "path": "tags"
                        },
                        "aggs": {
                            "tags": {
                                "terms": {
                                    "field": "tags.name",
                                    "size": 100
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
    tags = es.search(index=settings.ELASTIC_SEARCH['INDEX'], body=query)
    formatted_tags = []
    for tag in tags['aggregations']['category_tags']['nested_tags']['tags']['buckets']:
        formatted_tags.append(tag['tags_src']['hits']['hits'][0]['_source'])
    return formatted_tags


def get_categories():
    query = {
        "size": 0,
        "aggs": {
            "category": {
                "terms": {"field": "category.name", "size": 100},
                "aggs": {
                    "category_src": {
                        "top_hits": {
                            "size": 1,
                            "sort": [{"created_at": {"order": "desc"}}],
                            "_source": {
                                "includes": [
                                    "name",
                                    "name_slug",
                                    "products",
                                    "category",
                                ]
                            },
                        }
                    },
                },
            }
        },
    }
    elastic_categories = es.search(index=settings.ELASTIC_SEARCH["INDEX"], body=query)
    categories = []
    for category in elastic_categories["aggregations"]["category"]["buckets"]:
        source = {
            "pk": category["category_src"]["hits"]["hits"][0]["_id"],
            **category["category_src"]["hits"]["hits"][0]["_source"],
        }
        categories.append(source)

    return categories


def get_facets(params):
    """
    Метод выполняет агрегации фасетных данных
    1. Метод формирует фильтрующий запрос, основанный на предоставленных параметрах поиска
    2. Логика агрегаций для строковых фасетов: 
    Для каждого выбранного значения фасета метод выполняет дополнительный запрос,
    исключающий это значение из filter_query. Это необходимо для вывода всех возможных вариантов
    внутри текущего запроса(например, показать все доступные страны при выбранном стиле и наоборот)
    3. Логика агрегаций для числовых фасетов: Метод выполняет две агрегации:
    Контекстуальная агрегация (filtered_stats): использует filter_query для статистики по выборке
    Общая агрегация для числовых фасетов (all_stats): игнорирует filter_query и вычисляет общую статистику
    """
    filter_query = _create_filter_query(params)
    query = {
        "aggs": {
            "facets_filter": {
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
                                    "size": 100,
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
                                                    "size": 10
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
                    },
                    "number_facets": {
                        "nested": {"path": "number_facets"},
                        "aggs": {
                            "facets_code": {
                                "terms": {
                                    "field": "number_facets.slug",
                                    "size": 100,
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
            },
            "all_number_facets": {
                "nested": {"path": "number_facets"},
                "aggs": {
                    "facets_code": {
                        "terms": {
                            "field": "number_facets.slug",
                            "size": 100,
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
    all_facets = es.search(index=settings.ELASTIC_SEARCH['INDEX'], body=query)

    string_facets = []
    for string_facet_aggs in all_facets['aggregations']['facets_filter']['string_facets']['facets_code']['buckets']:
        facet_key = string_facet_aggs['key']
        facet_name = string_facet_aggs['facets_src']['hits']['hits'][0]['_source']['name']
        facet_pk = string_facet_aggs['facets_src']['hits']['hits'][0]['_id']
        string_facet_items = []
        for facet_item in string_facet_aggs['facets_nested']['facet_values']['buckets']:
            string_facet_obj = facet_item['facet_values_src']['hits']['hits'][0]['_source']
            string_facet_obj['count'] = facet_item['doc_count']
            string_facet_items.append(string_facet_obj)
        string_facets_obj = {
            'pk': facet_pk,
            'slug': facet_key,
            'values': string_facet_items,
            'name': facet_name
        }
        string_facets.append(string_facets_obj)

    sfilters = params.get('sfacets', None)
    if sfilters is not None:
        for sfilter in sfilters:
            attribute, values = sfilter
            sp_string_facet_items = _get_special_agg_values(params, attribute)
            facet_index = next((index for (index, d) in enumerate(string_facets) if d['slug'] == attribute), None)
            if facet_index is not None:
                string_facets[facet_index]['values'] = sp_string_facet_items

    number_facets = []
    tmp_all_number_facets = all_facets['aggregations']['all_number_facets']['facets_code']['buckets']
    all_number_facets = {item['key']: item['facets_stats'] for item in tmp_all_number_facets}
    for number_facet_aggs in all_facets['aggregations']['facets_filter']['number_facets']['facets_code']['buckets']:
        source = number_facet_aggs['facets_src']['hits']['hits'][0]['_source']
        facet_pk = number_facet_aggs['facets_src']['hits']['hits'][0]['_id']
        stats = number_facet_aggs['facets_stats']
        all_stats = all_number_facets[source['slug']]
        number_facets_obj = {
            'pk': facet_pk,
            'slug': source['slug'],
            'name': source['name'],
            'suffix': source['suffix'],
            'filtered_stats': {
                'min': _format_number(stats['min']),
                'max': _format_number(stats['max']),
            },
            'total_stats': {
                'min': _format_number(all_stats['min']),
                'max': _format_number(all_stats['max']),
            },

        }
        number_facets.append(number_facets_obj)

    return string_facets, number_facets


def _create_product_info_source(product):
    sfacets = []
    tmp_sfacets = product['sfacets']
    tmp_sfacets.sort(key=lambda elem: elem['facet']['pk'])
    groups = itertools.groupby(tmp_sfacets, lambda elem: elem['facet'])
    fulltext_sfacets = []

    for facet, values in groups:
        # При удалении параметра is_active у оригинального словаря facet нарушается группировка
        tmp_facet = dict(facet)
        tmp_facet.pop('is_active', None)
        tmp_facet['values'] = [{'pk': value['pk'], 'name': value['name']} for value in values]
        fulltext_sfacet_values = ' '.join([value['name'] for value in tmp_facet['values']])
        fulltext_sfacets.append(fulltext_sfacet_values)
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
            #'position': nfacet_model.extra['order'],
            'value': nfacet['value'],
        })
    
    # TODO make completion (suggest) on full string. now working only from beggining of completion
    completion = ' '.join([
        product['name'],
        product['manufacturer']['name'],
    ])

    tags_str = ' '.join([tag['name'] for tag in tags])
    sfacets_str = ' '.join(fulltext_sfacets)

    fulltext_russian = ' '.join([
        product['extra']['name_locale'],
        product['extra']['style_locale'],
        tags_str,
        sfacets_str,
        product['category']['name'],
    ])
    
    source = {
        'product_info_pk': product['pk'],
        'name': product['name'],
        'name_slug': product['name_slug'],
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
        'string_facets': sfacets,
        'number_facets': nfacets,
        'created_at': product['created_at'],
        'name_locale': product['extra']['name_locale'],
        'style_locale': product['extra']['style_locale'],
        'completion': completion,
        'suggest': completion,
        'fulltext_phonetic': completion,
        'fulltext_russian': fulltext_russian,
    }

    return source


# Values in loop is equivalent AND operator and have term in filter query
# Values as array of pk's is equivalent OR operator and have terms in filter query
def _create_filter_query(params, special_sfacet=None):
    filter_query = []

    category = params.get('category', None)
    if category is not None:
        category_query = {'term': {'category.slug': category}}
        filter_query.append(category_query)

    tags = params.get('tags', None)
    if tags is not None:
        tags_query = []
        for tag in tags:
            tag_query = {
                "nested": {
                    "path": "tags",
                    "query": {
                        "bool": {"filter": {"term": {"tags.pk": tag}}}
                    }
                }
            }
            tags_query.append(tag_query)
        filter_query.append(tags_query)

    sales = params.get('sales', None)
    if sales is not None:
        sale_query = {
            "nested": {
                "path": "instance.sales",
                "query": {
                    "bool": {
                        "filter": {
                            "terms": {"instance.sales.pk": sales}
                        }
                    }
                }
            }
        }
        filter_query.append(sale_query)

    collections = params.get('collections', None)
    if collections is not None:
        collection_query = {
            "bool": {
                "filter": {
                    "terms": {"instance.collections": collections}
                }
            }
        }
        filter_query.append(collection_query)

    string_facets_params = params.get('sfacets', None)
    if string_facets_params is not None:
        sfacet_query = []
        for string_facets_param in string_facets_params:
            attribute, values = string_facets_param
            if special_sfacet is not None and special_sfacet == attribute:
                continue
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

    number_facets_params = params.get('nfacets', None)
    if number_facets_params is not None:
        nfacet_query = []
        for number_facets_param in number_facets_params:
            attribute, values = number_facets_param
            min_val, max_val = values
            facet = {
              "nested": {
                "path": "number_facets",
                "query": {
                  "bool": {
                    "filter": [
                      {"term": {"number_facets.slug": attribute}},
                      {
                        "range" : {
                          "number_facets.value": {
                              "gte": min_val,
                              "lte": max_val
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


def _create_special_aggs_query(params, special_sfacet, size=10):
    filter_query = _create_filter_query(params, special_sfacet)
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
                    "filter": {"term": {"string_facets.slug": special_sfacet}},
                    "aggs": {
                      "nested_values": {
                        "nested": {
                          "path": "string_facets.values"
                        },
                        "aggs": {
                            "facets_values": {
                              "terms": {
                                  "field": "string_facets.values.pk",
                                  "size": size
                              },
                              "aggs": {
                                "values_src": {
                                  "top_hits": {
                                    "size": 1,
                                    "_source": {"includes": ["string_facets.values.pk", "string_facets.values.name"]}
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


def _get_special_agg_values(params, special_sfacet, size=10):
    special_agg_query = _create_special_aggs_query(params, special_sfacet, size)
    special_aggs = es.search(body=special_agg_query)
    sp_string_facet_values = []
    for bucket in special_aggs['aggregations']['special_agg']['nested_agg']['string_facets_agg']['nested_values']['facets_values']['buckets']:
        sp_string_facets_obj = bucket['values_src']['hits']['hits'][0]['_source']
        sp_string_facets_obj['count'] = bucket['doc_count']
        sp_string_facet_values.append(sp_string_facets_obj)
    return sp_string_facet_values


def get_sfacet_all_values(params, sfacet):
    facet_values = _get_special_agg_values(params, sfacet, size=100)
    return facet_values


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


def delete_category(category):
    body = {"query": {"term": {"category.pk": category['pk']}}}
    es.delete_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


def delete_manufacturer(manufacturer):
    body = {"query": {"term": {"manufacturer.pk": manufacturer['pk']}}}
    es.delete_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


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
    es.update_by_query(index=settings.ELASTIC_SEARCH['INDEX'], body=body)


def create_index():
    body = {
        "settings": {
            "index": {
            "number_of_shards": 1,
            "number_of_replicas": 1
            },
            "analysis": {
            "filter": {
                "my_phonetic_cyrillic": {
                "type": "phonetic",
                "encoder": "beider_morse",
                "rule_type": "approx",
                "name_type": "generic",
                "languageset": ["cyrillic"]
                },
                "my_phonetic_english": {
                "type": "phonetic",
                "encoder": "beider_morse",
                "rule_type": "approx",
                "name_type": "generic",
                "languageset": ["english"]
                },
                "russian_stop": {
                "type": "stop",
                "stopwords": "_russian_"
                },
                "dubbel_edge_ngram": {
                "type": "edgeNGram",
                "min_gram": "3",
                "max_gram": "10"
                },
                "russian_hunspell": {
                "type": "hunspell",
                "locale": "ru_RU"
                }
            },
            "analyzer": {
                "dubbel_phonetic": {
                "tokenizer": "standard",
                "filter": ["lowercase", "my_phonetic_english", "my_phonetic_cyrillic"]
                },
                "dubbel_hunspell": {
                "tokenizer": "standard",
                "filter": ["lowercase", "russian_stop", "russian_hunspell"]
                },
                "dubbel_edge": {
                "tokenizer": "standard",
                "filter": ["lowercase", "russian_stop", "dubbel_edge_ngram"]
                }
            }
            }
        },
        "mappings": {
            "properties": {
                "name": {
                "type": "keyword"
                },
                "name_slug": {
                "type": "keyword"
                },
                "manufacturer": {
                "type": "object",
                "properties": {
                    "pk": { "type": "integer" },
                    "slug": { "type": "keyword" },
                    "name": { 
                    "type": "keyword"
                    }
                }
                },
                "category": {
                "type": "object",
                "properties": {
                    "pk": { "type": "integer" },
                    "slug": { "type": "keyword" },
                    "name": {
                    "type": "keyword"
                    }
                }
                },
                "description": {
                "type": "text",
                "index": False
                },
                "tags": { 
                "type": "nested",
                "properties": {
                    "name": {
                    "type": "keyword"
                    },
                    "pk": { "type": "integer" }
                }
                },
                "count_instances" : {
                "type": "keyword"
                },
                "instance": {
                "type": "object",
                "properties": {
                    "pk": { "type": "integer" },
                    "sku": { "type": "integer" },
                    "measure": { "type": "integer" },
                    "base_price": { "type": "scaled_float", "scaling_factor": 100 },
                    "price": { "type": "scaled_float", "scaling_factor": 100 },
                    "stock_balance": { "type": "integer" },
                    "package_amount": { "type": "short" },
                    "capacity_type": { "type": "keyword" },
                    "images": {
                    "type": "nested",
                    "properties": {
                        "is_main": { "type": "boolean", "index": False },
                        "src": { "type": "keyword", "index": False }
                    }
                    },
                    "collections": { "type": "integer" },
                    "sales": { 
                    "type": "nested",
                    "properties": {
                        "pk": { "type": "integer" },
                        "name": { "type": "keyword" },
                        "date_start" : { "type": "date" },
                        "date_end" : { "type": "date" },
                        "type": { "type": "keyword" },
                        "percent": { "type": "scaled_float", "scaling_factor": 100 },
                        "fixed": { "type": "scaled_float", "scaling_factor": 100 },
                        "condition": { "type": "keyword" }
                    }
                    }
                }
                },
                "string_facets": {
                "type": "nested",
                "properties": {
                    "slug": { "type": "keyword" },
                    "name": { "type": "keyword" },
                    "pk": { "type": "integer" },
                    "values": {
                    "type": "nested",
                    "properties": {
                        "name": {
                        "type": "keyword"
                        },
                        "pk": { "type": "integer" }
                    }
                    }
                }
                },
                "number_facets": {
                "type": "nested",
                "properties": {
                    "pk": { "type": "integer" },
                    "slug": { "type": "keyword" },
                    "name": { "type": "keyword" },
                    "value": { "type": "scaled_float", "scaling_factor": 1000 },
                    "suffix": { "type": "keyword" }
                }
                },
                "created_at": {
                "type": "date"
                },
                "completion": {
                "type": "completion"
                },
                "suggest": {
                "type": "text"
                },
                "fulltext_phonetic": {
                "type": "text",
                "analyzer": "dubbel_phonetic"
                },
                "fulltext_russian": {
                "type": "text",
                "analyzer": "dubbel_hunspell",
                "fields": {
                    "edge": {
                    "type": "text",
                    "analyzer": "dubbel_edge"
                    }
                }
                }
            }
        }
    }
    es.indices.create(index=settings.ELASTIC_SEARCH['INDEX'], body=body)

def delete_index():
    try:
        es.indices.delete(index=settings.ELASTIC_SEARCH['INDEX'])
    except exceptions.NotFoundError:
        pass


def _format_number(number):
    number = float(number)
    return int(number) if number.is_integer() else number

