from elasticsearch import Elasticsearch
from django.conf import settings


es = Elasticsearch([settings.ELASTIC_SEARCH["CONFIG"]])


def search_products(params):
    filter_query = _create_filter_query(params)

    sort_name, sort_type = params.get('sort')
    sort_query = {sort_name: sort_type}

    page = params.get('page')
    page_from = settings.ELASTIC_SEARCH["PAGE_SIZE"] * (page - 1)

    query = {
        '_source': {
            'excludes': ['suggest', 'completion', 'fulltext_russian', 'fulltext_phonetic']
        },
        'query': {
            'bool': filter_query
        },
        'sort': sort_query,
        'from': page_from,
        'size': settings.ELASTIC_SEARCH["PAGE_SIZE"],
    }

    products = es.search(index=settings.ELASTIC_SEARCH["INDEX"], body=query)

    total_products = products['hits']['total']['value']

    formatted_products = []
    for product in products['hits']['hits']:
        source = product['_source']
        source['pk'] = product['_id']
        formatted_products.append(source)
    return {
        'items': formatted_products,
        'total': total_products,
    }


def complete_products(params):
    prefix = params.get('prefix')
    query = {
        "suggest": {
            "search-suggest": {
                "prefix": prefix,
                "completion": {
                    "field": "completion",
                    "skip_duplicates": True
                }
            }
        }
    }

    completions = es.search(index=settings.ELASTIC_SEARCH["INDEX"], body=query)

    formatted_completions = []
    for completion in completions['suggest']['search-suggest'][0]['options']:
        formatted_completions.append(completion['text'])

    return formatted_completions


def _create_filter_query(params):
    query = params.get('q')
    return {
        "should": [
            {
                "multi_match": {
                    "fields": [
                        "name^2",
                        "manufacturer.name^2",
                        "category.name"
                    ],
                    "operator": "AND",
                    "type": "cross_fields",
                    "query": query
                }
            },
            {
                "match": {
                    "fulltext_phonetic": {
                        "operator": "AND",
                        "query": query
                    }
                }
            },
            {
                "match": {
                    "fulltext_russian": {
                        "operator": "AND",
                        "query": query
                    }
                }
            },
            {
                "match": {
                    "fulltext_russian.edge": {
                        "operator": "AND",
                        "query": query
                    }
                }
            }
        ]
    }
