import inspect
import asyncio

import aiohttp
import aiohttp.client_exceptions
from parsel import Selector

from .utils.responsetypes import responsetypes
from .utils.loadobject import load_object
from .http import Request, Response
from .exceptions import DropItem

import logging
logger = logging.getLogger(__name__)


class Spider:

    def __init__(self, request=None, callback=None, pipeline=None, **kw):
        self.loop = kw.pop('loop', asyncio.get_event_loop())
        self.request  = request
        self.pipeline = self.build_pipeline(pipeline)

        if callback is None:
            self.callback = self.parse

        # let caller put arbitrary values in us, careful about overriding
        # something important
        for name, value in kw.items():
            setattr(self, name, value)

    def build_pipeline(self, pipeline):
        """
        if pipeline members are strings then load them
        else assure that they're coroutines
        """
        if pipeline is None:
            return []

        ret = []

        for p in pipeline:
            if isinstance(p, str):
                p = load_object(p)

            if inspect.isclass(p):
                assert asyncio.iscoroutinefunction(getattr(p, 'process_item'))
                p = p() # instantiate class
            else:
                assert asyncio.iscoroutinefunction(p)

            ret.append(p)

        return ret

    async def parse(self, response):
        raise NotImplementedError("%s().parse() not implemented", self.__class__.__name__)

    async def fetch(self, client, url):
        """
        return resp & body or None if error
        """
        try:
            async with client:
                resp = await client.get(url)

                if resp.status > 299:
                    logger.error("%s returned %d", url, resp.status)
                    return resp, None

                return resp, await resp.read()

        except aiohttp.client_exceptions.ClientError as e:
            logger.error("url: %s: error: %s", url, e)

        return None, None

    async def crawl(self, request=None, callback=None, client=None):
        """
        main function, this is an async generator, must "call" with a for loop

        async for item in Spider.crawl():
            pass

        yields items, aka results of passing through callback and pipeline

        request: str or Request
        callback: async generator
        client: ClientSession
        """
        request = request or self.request
        assert request

        # convert string url to a Request
        if not isinstance(request, Request):
            request = Request(request)

        callback = request.callback or callback or self.callback
        assert inspect.isasyncgenfunction(callback), "callback must be an async generator (async with yield)"

        if client is None:
            client = aiohttp.ClientSession()

        resp, body = await self.fetch(client, request.url)

        if resp is None or body is None:
            logger.error("can not proceed from: %s", request.url)
            return

        # make an appropriate response object (HtmlResponse, TextResponse, etc)
        # probably an HtmlResponse
        respcls = responsetypes.from_args(headers=resp.headers, url=request.url, body=body)
        response = respcls(url=request.url, status=resp.status, headers=resp.headers, body=body)

        async for item in self.handle_response(response, callback):
            yield item

    async def handle_response(self, response, callback):
        """
        pass the response to the callback (likely self.parse()) and
        take it's emitted items and pass them to our pipeline

        start another request if we receive a Request, this is how
        a site can "spider"
        """
        async for item in callback(response):
            if isinstance(item, Request):
                async for item in self.crawl(item, callback):
                    yield item
            else:
                item = await self.handle_pipeline(item, response)

                if item is None:
                    continue

                yield item

    async def handle_pipeline(self, item, response):
        """
        pass item through provided pipeline, a pipeline stage
        can return the item, or raise DropItem
        """
        if item is None:
            return None

        for p in self.pipeline:
            try:
                # logger.debug(p)
                if getattr(p, 'process_item', False):
                    item = await p.process_item(response, self, item)
                else:
                    item = await p(response, self, item)

            except DropItem as e:
                logger.warn("%s: dropping item: %s", p.__class__.__name__, e)
                return None

            except Exception as e:
                logger.error("%s: exception: %s", p.__class__.__name__, e)
                logger.exception(e)
                return None

        # if item is not None:
        #     logger.debug(f"finished pipeline for: {item}")

        return item
