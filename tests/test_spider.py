import pytest_aiohttp
import aiohttp
import asyncio
import pytest

from iterweb import Spider, Response

from . import get_next, client, exhaust

def test_init_empty(client):
    s = Spider()
    assert s.callback is not None

async def test_enqueue_1(client):
    s = Spider()
    await s.enqueue('url')
    assert not s.queue.empty()

async def test_enqueue_2(client):
    async def parse(response):
        yield None

    s = Spider(parse_func=parse)
    await get_next(s.crawl('/beast', client=client))
    assert s.queue.empty()

async def test_parse_is_implemented(client):

    s = Spider()
    gen = s.crawl('/beast', client=client)
    # with pytest.raises(AssertionError):
    #     await get_next(gen)
    with pytest.raises(NotImplementedError):
        await get_next(gen)

async def test_pipeline_1(client):

    async def p1(spider, response, item):
        assert isinstance(spider, Spider)
        assert isinstance(response, Response)
        assert isinstance(item, int)
        assert item == 0
        return 1

    async def parse(response):
        yield 0

    s = Spider(parse_func=parse, pipeline=[p1])
    gen = s.crawl('/beast', client=client)
    item = await get_next(gen)

    assert item == 1
    await exhaust(gen)

async def global_p1(spider, response, item):
    return 1

async def test_pipeline_2(client):

    async def parse(response):
        yield 0

    s = Spider(parse_func=parse, pipeline=['tests.test_spider.global_p1'])
    gen = s.crawl('/beast', client=client)
    item = await get_next(gen)

    assert item == 1
    await exhaust(gen)

async def test_coro_parse(client):
    """
    this tests convert_to_generator in handle_response
    """
    item = 0

    async def do_work():
        nonlocal item
        item += 1

    async def parse(response):
        """
        instead of yielding a request or item just
        do some work instead. This also tests that
        returning a value propagates back as well.
        """
        await asyncio.gather(do_work(), do_work())
        return 1

    s = Spider(parse_func=parse)
    gen = s.crawl('/beast', client=client)
    r = await get_next(gen)

    assert item == 2
    assert r == 1
    await exhaust(gen)

async def test_exhaust(client):
    called = False

    async def parse(response):
        nonlocal called
        called = True
        # yield or return here works fine

    s = Spider(parse_func=parse)
    await s.exhaust('/beast', client=client)

    assert called == 1

async def test_inheritance(client):
    called = False

    class MySpider(Spider):
        async def parse(self, response):
            nonlocal called
            called = True
            yield

    s = MySpider()
    await s.exhaust('/beast', client=client)


async def test_tracking(client):
    item = 0

    async def parse(response):
        nonlocal item
        item += 1
        assert 'redeye' in response.text
        yield 'foo'

    s = Spider(parse_func=parse, track_urls=True)
    await s.exhaust(['/beast', '/beast'], client=client)

    assert item == 1
