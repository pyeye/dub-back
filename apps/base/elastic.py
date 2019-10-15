from elasticsearch import Elasticsearch

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