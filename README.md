# iterweb

Iterator Web thingy.

This is a budget version of [scrapy](https://scrapy.org/) but with a few features:

* written using asyncio
* `iterweb` is _pull_ while `scrapy` is more _push_
* `Spider.crawl()` is an async generator
* purely a library, no callable scripts

Similarities to scrapy:

* uses scrapy `Request` and `Response` objects
* uses the concept of a pipeline
* yield a `Request` to get another page

## usage

```python
import asyncio
import iterweb

import logging
logger = logging.getLogger(__name__)

class ImgSpider(iterweb.Spider):
    """
    yields all img urls in response
    """
    async def parse(self, response):
        logger.debug("parsing: %s", response.url)

        for img in response.xpath('//img'):
            src = img.xpath('@src').get()
            yield src


class StageUrlJoin:
    """
    convert potential relative url to absolute url
    """
    async def process_item(self, spider, response, url):
        url = response.urljoin(url)
        return url


async def get_pics(url):
    pipeline = [
        '__main__.StageUrlJoin',
    ]

    loop = asyncio.get_event_loop()
    spider = ImgSpider(loop=loop, pipeline=pipeline)

    async for img_url in spider.crawl(url):
        print(img_url)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_pics('https://www.google.com'))
```
