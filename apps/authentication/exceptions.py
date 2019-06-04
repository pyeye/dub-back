from rest_framework.exceptions import APIException

class TokenExpire(APIException):
    status_code = 498
    default_detail = 'Access token expire.'
    default_code = 'authentication_failed'