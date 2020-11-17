from functools import partial
import inspect
import asyncio

import aiohttp
import aiohttp.client_exceptions

from .pipeline import Pipeline
from .reqresp import Request, Response

import logging
logger = logging.getLogger(__name__)


def is_async(func):
    # python 3.8 changed how an async function is passed through a functools.partial
    # so "follow" any nested partials to get to the "real" function and test that
    while isinstance(func, partial):
        func = func.func
    return inspect.isasyncgenfunction(func) or asyncio.iscoroutinefunction(func)

class Spider:

    def __init__(self, **kw):

        self.loop = kw.pop('loop', asyncio.get_event_loop())
        self.callback = kw.pop('parse_func', self.parse)

        stages = kw.pop('pipeline', [])
        self.pipeline = Pipeline(stages)

        self.queue = asyncio.Queue()

        # this is a bit of a misnomer, we only track at enqueuing time
        # and success/failure or ultimate fetch is not taken into account
        self.track_urls = kw.pop('track_urls', True)
        self.visted_urls = set() # probably visited

        # let caller put arbitrary attributes in us, careful about overriding
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
            # convert url string to a Request
            if not isinstance(request, Request):
                request = Request(request, callback=self.callback)

            if self.track_urls:
                if request.url in self.visted_urls:
                    continue
                else:
                    self.visted_urls.add(request.url)

            await self.queue.put(request)

    async def fetch(self, session, url):
        """
        return resp & body or None if error
        """

        # making a new session for each fetch is not ideal but there is
        # a bug with ssl and/or asyncio which spews a bunch of errors when
        # the program exits. Everything does work however.
        # https://github.com/aio-libs/aiohttp/issues/4324

        try:
            async with session.get(url) as resp:
                resp.raise_for_status()
                resp._body = await resp.read() # set coro with value, this is allowed
                resp.close()
                return resp

        except (aiohttp.ClientResponseError, aiohttp.client_exceptions.ClientError) as e:
            logger.error("url: %s: %s - error: %s", url, resp.status, e)

        return None

    async def exhaust(self, *args, **kw):
        """
        call self.crawl() but don't yield results, this is
        useful if self.parse() and/or pipeline does work.

        eg. await spider.exhaust(urls)
        """
        async for _ in self.crawl(*args, **kw):
            pass

    async def crawl(self, requests, client=None):
        try:
            if client is None:
                client = aiohttp.ClientSession(
                    loop=self.loop,
                    headers={'Connection': 'keep-alive'}
                )
                close_client = True
            else:
                close_client = False

            async for item in self._crawl(requests, client):
                yield item

        finally:
            if close_client and not client.closed:
                await client.close()

    async def _crawl(self, requests, client):
        """
        main function, this is an async generator, must "call" with a for loop

        async for item in Spider.crawl(url):
            pass

        the response is passed to self.parse and the output of self.parse
        is sent to the pipeline. The result of the pipeline is returned

        request: str or Request
        client_factory: function that returns aiohttp.ClientSession
        """
        await self.enqueue(requests)

        async with client as session:

            while not self.queue.empty():
                tasks = []
                requests = []

                # empty the queue to start all fetches, any callback
                # may add to the queue to keep outer loop going
                while not self.queue.empty():
                    request = await self.queue.get()

                    task = self.loop.create_task(
                        self.fetch(session, request.url)
                    )

                    tasks.append(task)
                    requests.append(request)

                for request, task in zip(requests, tasks):
                    resp = await task

                    if resp is None:
                        logger.error("can not proceed with: %s", request.url)
                        continue

                    resp = Response(request.url, resp)
                    callback = request.callback or self.callback

                    # I've forgetten the async keyword too many times
                    assert is_async(callback), f"{callback.__name__} must be async"

                    async for item in self.handle_response(callback, resp):
                        yield item

    async def handle_response(self, callback, response):
        """
        pass the response to the callback (likely self.parse) and
        pass the emitted items to our pipeline

        start another request if we receive a Request, this is how
        a site can get crawled
        """
        async def convert_to_generator(callback, response):
            yield await callback(response)

        # if the callback is not a generator, then convert it
        # to one so that we can use it in the loop below
        if not inspect.isasyncgenfunction(callback):
            callback = partial(convert_to_generator, callback)

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
