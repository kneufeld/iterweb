from urllib.parse import urljoin

import aiohttp.web
from parsel import Selector

from .utils.reify import reify

import logging
logger = logging.getLogger(__name__)

class Request:
    def __init__(self, url, *args, **kw):
        self.url = url
        self.callback = kw.pop('callback', None)

class Response:
    """
    wrap an aiohttp.ClientResponse with extra functionality
    but pass any getattr to it
    """

    def __init__(self, url, response):
        self.url = url
        self._response = response # aiohttp.ClientResponse

    def __getattr__(self, name):
        return getattr(self._response, name)

    @property
    def body(self):
        return self._body

    @reify
    def text(self):
        """
        convert body (bytes) to a string by using response encoding or utf-8
        """
        # can't use self._response.text as it's a coro, calls the equivalent though
        return self._body.decode(self._response.get_encoding() or 'utf-8')

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
