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
        raise NotImplementedError("%s().parse() not implemented", self.__class__.__name__)

    async def enqueue(self, urls):
        if not urls:
            return

        if not isinstance(urls, list):
            urls = [urls]

        for url in urls:
            # convert Request to its url, happens if self.parse yields a Request
            if isinstance(url, Request):
                url = url.url

            await self.queue.put(url)

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

    async def crawl(self, urls, client_factory=None):
        """
        main function, this is an async generator, must "call" with a for loop

        async for item in Spider.crawl(url):
            pass

        the response is passed to self.parse and the output of self.parse
        is sent to the pipeline. The result of the pipeline is returned

        request: str or Request
        client_factory: function that returns aiohttp.ClientSession
        """
        assert inspect.isasyncgenfunction(self.callback), \
        "self.parse must be an async generator (async with yield)"

        await self.enqueue(urls)

        if client_factory is None:
            client_factory = lambda: aiohttp.ClientSession(
                loop=self.loop,
                raise_for_status=True
            )

        while not self.queue.empty():
            url = await self.queue.get()
            resp = await self.fetch(client_factory, url)

            if resp is None or resp.text is None:
                logger.error("can not proceed with: %s", url)
                continue

            resp = Response._copy_response(url, resp)

            async for item in self.handle_response(resp):
                yield item

    async def handle_response(self, response):
        """
        pass the response to the self.parse (likely self.parse()) and
        take it's emitted items and pass them to our pipeline

        start another request if we receive a Request, this is how
        a site can "spider"
        """
        async for item in self.callback(response):
            if isinstance(item, Request):
                await self.enqueue(item.url)
            else:
                item = await self.pipeline.process(self, response, item)

                if item is None:
                    continue

                yield item
