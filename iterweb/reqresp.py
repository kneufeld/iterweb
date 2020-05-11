from urllib.parse import urljoin

import aiohttp.web
from parsel import Selector

from .utils.reify import reify

class Request:
    def __init__(self, url, *args, **kw):
        self.url = url
        self.callback = kw.pop('callback', None)

class Response:
    """
    wrap an aiohttp.Response with extra functionality
    but pass any getattr to it
    """

    def __init__(self, url, response):
        self.url = url
        self._response = response

    def __getattr__(self, name):
        return getattr(self._response, name)

    @property
    def body(self):
        return self._body

    @property
    def text(self):
        if isinstance(self._body, bytes):
            return self._body.decode('utf-8')
        else:
            return self._body

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
