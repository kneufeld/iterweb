import pytest

from iterweb import Spider

from . import get_next, beast, redeye

def test_init_empty():
    s = Spider()
    assert s.callback is None

def test_init_callback():
    s = Spider(callback=lambda _: _)
    assert s.callback is not None

@pytest.mark.asyncio
async def test_pipeline_1():

    async def p1(item, response, spider):
        assert item == 0
        return 1

    async def parse(response):
        yield 0

    s = Spider(beast, callback=parse, pipeline=[p1])
    gen = s.crawl()
    item = await get_next(gen)

    assert item == 1

async def global_p1(item, response, spider):
    return 1

@pytest.mark.asyncio
async def test_pipeline_2():

    async def parse(response):
        yield 0

    s = Spider(beast, callback=parse, pipeline=['tests.test_spider.global_p1'])
    gen = s.crawl()
    item = await get_next(gen)

    assert item == 1
