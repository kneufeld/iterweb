import aiohttp
import pytest

from iterweb import Spider, Request, Response

from . import get_next, exhaust, client

async def test_crawl(client):
    called = False

    async def parse(response):
        nonlocal called
        called = True
        yield {'value': 'value'}

    s = Spider(parse_func=parse)
    gen = s.crawl('/beast', client=client)
    item = await get_next(gen)

    assert called
    assert item['value'] == 'value', "not called back"
    await exhaust(gen)

async def test_get_recursive(client):

    async def parse(response):
        if 'beast' in response.url:
            yield Request('/google')

        if 'google' in response.url:
            yield 'google'

    s = Spider(parse_func=parse)
    gen = s.crawl('/beast', client=client)
    item = await get_next(gen)

    assert item == 'google'
    await exhaust(gen)

async def test_get_redeye(client):

    async def parse(response):
        for img in response.xpath('//img'):
            src = img.xpath('@src').extract_first()
            src = response.urljoin(src)
            yield src

    s = Spider(parse_func=parse)
    gen = s.crawl('/beast', client=client)
    item = await get_next(gen)

    assert 'redeye' in item
    await exhaust(gen)

async def test_crawl_page_1(client):

    async def parse(response):
        yield 1
        yield 2
        yield 3

    s = Spider(parse_func=parse)
    gen = s.crawl('/beast', client=client)

    assert 1 == await get_next(gen)
    assert 2 == await get_next(gen)
    assert 3 == await get_next(gen)
    await exhaust(gen)

async def test_crawl_exception(client):

    async def parse(response):
        raise RuntimeError("test error")
        yield 1

    s = Spider(parse_func=parse)

    with pytest.raises(RuntimeError):
        async for item in s.crawl('/beast', client=client):
            pass
