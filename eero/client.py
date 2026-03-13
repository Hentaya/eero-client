import json
import re
import requests

from .exception import ClientException


class Client(object):
    API_ROOT = 'https://api-user.e2ro.com'
    API_ENDPOINT = API_ROOT + '/2.2/{}'

    def _parse_response(self, response):
        data = json.loads(response.text)
        if data['meta']['code'] != 200 and data['meta']['code'] != 201:
            raise ClientException(data['meta']['code'],
                                  data['meta'].get('error', ""))
        return data.get('data', "")

    def post(self, action, **kwargs):
        response = requests.post(self.API_ENDPOINT.format(action), **kwargs)
        return self._parse_response(response)

    def get(self, action, **kwargs):
        response = requests.get(self.API_ENDPOINT.format(action), **kwargs)
        return self._parse_response(response)

    def get_url(self, resource_url, **kwargs):
        if not isinstance(resource_url, str):
            raise ValueError('resource_url must be a string')

        if not re.match(r'^/2\.[0-9]+/', resource_url):
            raise ValueError('unexpected resource URL: {}'.format(resource_url))

        url = '{}{}'.format(self.API_ROOT, resource_url)
        response = requests.get(url, **kwargs)
        return self._parse_response(response)
