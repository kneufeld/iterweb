from urllib.parse import urljoin

import aiohttp.web
from parsel import Selector

from .utils.reify import reify

class Request:
    def __init__(self, url, *args, **kw):
        self.url = url

class Response(aiohttp.web.Response):

    def __init__(self, url, *args, **kw):
        body = kw.pop('body', None)
        super().__init__(*args, **kw)

        if body:
            self.body = body

        self.url = url

    @reify
    def selector(self):
        return Selector(self.text)

    def xpath(self, query, **kwargs):
        return self.selector.xpath(query, **kwargs)

    def css(self, query):
        return self.selector.css(query)

    def urljoin(self, url):
        """
        convert possible relative url to absolute based on request url
        """
        return urljoin(self.url, url)

    @staticmethod
    def clone(url, aio_resp):
        """
        convert the aiohttp response into our Response type
        """
        return Response(
            url,
            status=aio_resp.status,
            headers=aio_resp.headers,
            text=aio_resp.text,
        )
