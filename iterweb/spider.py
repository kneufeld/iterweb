import inspect
import asyncio

import aiohttp
import aiohttp.client_exceptions

from .pipeline import Pipeline
from .reqresp import Request, Response

import logging
logger = logging.getLogger(__name__)


class Spider:

    def __init__(self, **kw):

        self.loop = kw.pop('loop', asyncio.get_event_loop())
        self.callback = kw.pop('parse_func', self.parse)

        stages = kw.pop('pipeline', None)
        self.pipeline = Pipeline(stages)

        self.queue = asyncio.Queue(loop=self.loop)

        # let caller put arbitrary values in us, careful about overriding
        # something important
        for name, value in kw.items():
            setattr(self, name, value)

    async def parse(self, response):
        raise NotImplementedError("%s().parse() not implemented" % self.__class__.__name__)

    async def enqueue(self, requests):
        if not requests:
            return

        if not isinstance(requests, list):
            requests = [requests]

        for request in requests:
            # convert Request to its url, happens if self.parse yields a Request
            if not isinstance(request, Request):
                request = Request(request, callback=self.callback)

            await self.queue.put(request)

    async def fetch(self, client_factory, url):
        """
        return resp & body or None if error
        """

        # making a new session for each fetch is not ideal but there is
        # a bug with ssl and/or asyncio which spews a bunch of errors when
        # the program exits. Everything does work however.
        # https://github.com/aio-libs/aiohttp/issues/4324

        client = client_factory()

        try:
            async with client:
                resp = await client.get(url)
                resp.text = await resp.text() # set coro with value, this is allowed
                resp.close()
                return resp

        except (aiohttp.ClientResponseError, aiohttp.client_exceptions.ClientError) as e:
            logger.error("url: %s: error: %s", url, e)

        return None

    async def exhaust(self, *args, **kw):
        """
        call self.crawl() but don't yield results, this is
        useful if self.parse() and/or pipeline does work.

        eg. await spider.exhaust(urls)
        """
        async for _ in self.crawl(*args, **kw):
            pass

    async def crawl(self, requests, client_factory=None):
        """
        main function, this is an async generator, must "call" with a for loop

        async for item in Spider.crawl(url):
            pass

        the response is passed to self.parse and the output of self.parse
        is sent to the pipeline. The result of the pipeline is returned

        request: str or Request
        client_factory: function that returns aiohttp.ClientSession
        """

        # assert inspect.isasyncgenfunction(self.callback), \
        # "self.parse must be an async generator (async with yield)"

        await self.enqueue(requests)

        if client_factory is None:
            client_factory = lambda: aiohttp.ClientSession(
                loop=self.loop,
                raise_for_status=True
            )

        while not self.queue.empty():
            request = await self.queue.get()
            url = request.url
            callback = request.callback or self.callback

            resp = await self.fetch(client_factory, url)

            if resp is None or resp.text is None:
                logger.error("can not proceed with: %s", url)
                continue

            resp = Response.clone(url, resp)

            async for item in self.handle_response(callback, resp):
                yield item
                resp = Response(request.url, resp)

    async def handle_response(self, callback, response):
        """
        pass the response to the self.parse (likely self.parse()) and
        take it's emitted items and pass them to our pipeline

        start another request if we receive a Request, this is how
        a site can "spider"
        """
        from functools import partial
        async def _generator(callback, response):
            yield await callback(response)

        if not inspect.isasyncgenfunction(callback):
            callback = partial(_generator, callback)

        async for item in callback(response):
            if item is None:
                continue
            elif isinstance(item, Request):
                await self.enqueue(item)
            else:
                item = await self.pipeline.process(self, response, item)

                if item is None:
                    continue

                yield item
