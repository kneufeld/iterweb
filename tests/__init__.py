import pytest
import aiohttp

html_beast = """
<!DOCTYPE html>
<html>

  <head>
    <title>Beast</title>
  </head>

  <body>

<div class="wrapper">
  <div class="header">
    <img id="eye" src="/beast/static/images/redeye.16a3a3bc36e1.jpg">
    <img id="header_spacer" src="/beast/static/images/clear.69d5ca8d8198.png">
  </div>

  <p>A paragraph</p>

  </body>
</html>
"""

html_google = """
google's homepage
"""

@pytest.fixture
def client(loop, aiohttp_client):
    app = aiohttp.web.Application()
    app.router.add_get('/', lambda request: aiohttp.web.Response(text=html_beast))
    app.router.add_get('/beast', lambda request: aiohttp.web.Response(text=html_beast))
    app.router.add_get('/google', lambda request: aiohttp.web.Response(text=html_google))

    return loop.run_until_complete(aiohttp_client(app))

async def get_next(generator):
    """
    get the next page and pass to callback

    this should probably never be called...
    """
    try:
        item = await generator.__anext__()
        return item
    except StopAsyncIteration:
        return None

# https://github.com/aio-libs/aiohttp/issues/4684
async def exhaust(generator):
    async for _ in generator:
        pass
