from aiohttp import web

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

async def beast(request):
    return web.Response(text=html_beast)

async def test_hello(aiohttp_client, loop):
    app = web.Application()
    app.router.add_get('/', beast)
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    text = await resp.text()
    assert 'Beast' in text
