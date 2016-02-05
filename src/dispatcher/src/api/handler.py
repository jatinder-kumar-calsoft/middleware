import falcon
import json


class ApiHandler(object):
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.api = falcon.API()

    def __call__(self, environ, start_response):
        environ['PATH_INFO'] = environ.get('PATH_INFO', '').replace('/api/v2.0', '', 1)
        return self.api.__call__(environ, start_response)
