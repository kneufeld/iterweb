from urllib.parse import urljoin

import aiohttp.web
from parsel import Selector
from w3lib.encoding import (html_body_declared_encoding, html_to_unicode,
                            http_content_type_encoding, resolve_encoding)

from .utils.reify import reify

class Request:
    def __init__(self, url, *args, **kw):
        self.url = url

class Response(aiohttp.web.Response):

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

