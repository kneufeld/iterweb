beast = ""
redeye = ""

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
