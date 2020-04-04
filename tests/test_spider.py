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
