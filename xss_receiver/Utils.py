import random
from functools import wraps
from hashlib import sha256

from flask import Flask, Response, make_response, request


def random_string(len):
    return "".join(random.choices("0123456789abcdef", k=len))


def passwd_hash(str, salt):
    return sha256((str + salt).encode()).hexdigest()


def file_nocache(func):
    @wraps(func)
    def _nocache(*args, **kwargs):
        response = func(*args, **kwargs)
        if type(response) != Response:
            response = make_response(response)
        if 'ETag' in response.headers.keys():
            response.headers.pop('ETag')
            response.headers.pop('Last-Modified')

        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response

    return _nocache


class NoServerHeaderFlask(Flask):
    def process_response(self, response):
        super(NoServerHeaderFlask, self).process_response(response)
        response.headers['X-Powered-By'] = 'PHP/7.3.11'
        response.headers['Server'] = 'Apache/2.4.41 (Unix) PHP/7.3.11'
        return response
