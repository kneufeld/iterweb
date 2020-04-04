import inspect
import asyncio

import aiohttp
import aiohttp.client_exceptions

from .utils import load_object
from .reqresp import Request, Response
from . import DropItem, DropItemError

import logging
logger = logging.getLogger(__name__)


class Spider:

    def __init__(self, **kw):

        self.loop = kw.pop('loop', asyncio.get_event_loop())
        self.callback = kw.pop('parse_func', self.parse)

        pipeline = kw.pop('pipeline', None)
        self.pipeline = self.build_pipeline(pipeline)

        self.queue = asyncio.Queue(loop=self.loop)

        # let caller put arbitrary values in us, careful about overriding
        # something important
        for name, value in kw.items():
            setattr(self, name, value)

    async def parse(self, response):
        raise NotImplementedError("%s().parse() not implemented", self.__class__.__name__)

    def build_pipeline(self, pipeline):
        """
        if pipeline members are strings then load them
        else assure that they're coroutines
        """
        if pipeline is None:
            return []

        ret = []

        for stage in pipeline:
            if isinstance(stage, str):
                stage = load_object(stage)

            if inspect.isclass(stage):
                assert asyncio.iscoroutinefunction(getattr(stage, 'process_item'))
                stage = stage() # instantiate class
            else:
                assert asyncio.iscoroutinefunction(stage)

            ret.append(stage)

        return ret

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
        try:
            async with client:
                resp = await client.get(url)
                resp.text = await resp.text() # set coro with value, this is allowed
                return resp

        except (aiohttp.ClientResponseError, aiohttp.client_exceptions.ClientError) as e:
            logger.error("url: %s: error: %s", url, e)

        return None

    async def crawl(self, url, client=None):
        """
        main function, this is an async generator, must "call" with a for loop

        async for item in Spider.crawl(url):
            pass

        the response is passed to self.parse and the output of self.parse
        is sent to the pipeline. The result of the pipeline is returned

        request: str or Request
        client: aiohttp.ClientSession
        """
        # convert Request to its url, happens if self.parse yields a Request
        if isinstance(url, Request):
            url = url.url

        assert inspect.isasyncgenfunction(self.callback), \
        "self.parse must be an async generator (async with yield)"

        if client is None:
            client = aiohttp.ClientSession(raise_for_status=True)

        resp = await self.fetch(client, url)

        if resp is None or resp.text is None:
            logger.error("can not proceed from: %s", url)
            return

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
                item = await self.handle_pipeline(self.pipeline, response, item)

                if item is None:
                    continue

                yield item

    async def handle_pipeline(self, pipeline, response, item):
        """
        pass item through provided pipeline, a pipeline stage
        can return the item, or raise DropItem
        """
        if item is None:
            return None

        for stage in pipeline:
            try:
                # logger.debug(stage)
                if getattr(stage, 'process_item', False):
                    item = await stage.process_item(self, response, item)
                else:
                    item = await stage(self, response, item)

            except DropItem as e:
                # THINK should we be logging or the called function?
                logger.debug("%s: dropping item: %s", stage.__class__.__name__, e)
                return None

            except DropItemError as e:
                # THINK should we be logging or the called function?
                logger.error("%s: dropping item: %s", stage.__class__.__name__, e)
                return None

            except Exception as e:
                # THINK should we really be catching this?
                logger.error("%s: exception: %s", stage.__class__.__name__, e)
                logger.exception(e)
                return None

        return item
