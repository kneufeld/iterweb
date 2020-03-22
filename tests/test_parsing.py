import pytest

from iterweb import Spider, Request, Response

from . import get_next, beast, redeye

@pytest.mark.asyncio
async def test_crawl():
    called = False

    async def parse(response):
        nonlocal called
        called = True
        yield {'value': 'value'}

    s = Spider(parse_func=parse)
    gen = s.crawl(beast)
    item = await get_next(gen)

    assert called
    assert item['value'] == 'value', "not called back"

@pytest.mark.asyncio
async def test_get_recursive():

    async def parse(response):
        if 'beast' in str(response.url):
            yield Request('https://www.google.com')

        yield 'google'

    s = Spider(parse_func=parse)
    gen = s.crawl(beast)
    item = await get_next(gen)

    assert item == 'google'

@pytest.mark.asyncio
async def test_get_redeye():

    async def parse(response):
        for img in response.xpath('//img'):
            src = img.xpath('@src').extract_first()
            src = response.urljoin(src)
            yield src

    s = Spider(parse_func=parse)
    gen = s.crawl(beast)
    item = await get_next(gen)

    assert item == redeye

@pytest.mark.asyncio
async def test_crawl_page_1():

    async def parse(response):
        yield 1
        yield 2
        yield 3

    s = Spider(parse_func=parse)
    gen = s.crawl(beast)

    assert 1 == await get_next(gen)
    assert 2 == await get_next(gen)
    assert 3 == await get_next(gen)

@pytest.mark.asyncio
async def test_crawl_exception():

    async def parse(response):
        raise RuntimeError("test error")
        yield 1

    s = Spider(parse_func=parse)

    with pytest.raises(RuntimeError):
        async for item in s.crawl(beast):
            pass
