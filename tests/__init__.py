beast = "https://www2.burgundywall.com/beast/"
redeye = "https://www2.burgundywall.com/beast/static/images/redeye.16a3a3bc36e1.jpg"

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
