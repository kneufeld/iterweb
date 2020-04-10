import asyncio
import pytest

from iterweb import Spider, Response

from . import get_next, beast, redeye

def test_init_empty():
    s = Spider()
    assert s.callback is not None

@pytest.mark.asyncio
async def test_enqueue_1():
    s = Spider()
    await s.enqueue('url')
    assert not s.queue.empty()

@pytest.mark.asyncio
async def test_enqueue_2():
    async def parse(response):
        yield None

    s = Spider(parse_func=parse)
    await get_next(s.crawl(beast))
    assert s.queue.empty()

@pytest.mark.asyncio
async def test_parse_is_implemented():

    s = Spider()
    gen = s.crawl(beast)
    # with pytest.raises(AssertionError):
    #     await get_next(gen)
    with pytest.raises(NotImplementedError):
        await get_next(gen)

@pytest.mark.asyncio
async def test_pipeline_1():

    async def p1(spider, response, item):
        assert isinstance(spider, Spider)
        assert isinstance(response, Response)
        assert isinstance(item, int)
        assert item == 0
        return 1

    async def parse(response):
        yield 0

    s = Spider(parse_func=parse, pipeline=[p1])
    gen = s.crawl(beast)
    item = await get_next(gen)

    assert item == 1

async def global_p1(spider, response, item):
    return 1

@pytest.mark.asyncio
async def test_pipeline_2():

    async def parse(response):
        yield 0

    s = Spider(parse_func=parse, pipeline=['tests.test_spider.global_p1'])
    gen = s.crawl(beast)
    item = await get_next(gen)

    assert item == 1

@pytest.mark.asyncio
async def test_coro_parse():
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
    gen = s.crawl(beast)
    r = await get_next(gen)

    assert item == 2
    assert r == 1

@pytest.mark.asyncio
async def test_exhaust():
    called = False

    async def parse(response):
        nonlocal called
        called = True
        # yield or return here works fine

    s = Spider(parse_func=parse)
    await s.exhaust(beast)

    assert called == 1

@pytest.mark.asyncio
async def test_inheritance():
    called = False

    class MySpider(Spider):
        async def parse(self, response):
            nonlocal called
            called = True
            yield

    s = MySpider()
    await s.exhaust(beast)


@pytest.mark.asyncio
async def test_tracking():
    item = 0

    async def parse(response):
        nonlocal item
        item += 1

    s = Spider(parse_func=parse, track_urls=True)
    gen = s.crawl([beast, beast])
    await get_next(gen)

    assert item == 1
