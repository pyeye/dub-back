from elasticsearch import Elasticsearch

INDEX = 'products_dev'
CONFIG = {
    'host': 'elastic',
    'port': 9200,
    'http_auth': ('elastic', 'secret')
}

PAGE_SIZE = 4

es = Elasticsearch([CONFIG])


def elastic_search_products(params):
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
            'excludes': ['suggest', 'completion', 'fulltext_russian', 'fulltext_phonetic']
        },
        'query': {
            'bool': filter_query
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
        formatted_products.append(source)
    return {
        'items': formatted_products,
        'total': total_products,
    }

def elastic_complete_products(params):
    complete = params.get('complete')
    query = {
        "suggest": {
            "search-suggest" : {
                "prefix": complete,
                "completion" : {
                    "field" : "completion",
                    "fuzzy": True,
                    "skip_duplicates": True
                }
            }
        }
    }

    completions = es.search(index=INDEX, body=query)

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