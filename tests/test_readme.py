import os
import io
import imp

def extract_code(fpath):
    code = []
    started = False

    with open(fpath) as f:
        for line in f.readlines():
            if started and line.startswith('```'):
                break
            elif started:
                code.append(line)
            elif not started and line.startswith('```python'):
                started = True

    return "".join(code)

async def test_readme():
    """
    make sure example in readme.md works
    """
    fpath = os.path.join(os.path.dirname(__file__), '..', 'README.md')
    code = extract_code(fpath)
    code = io.StringIO(code)
    code.mode = 'b'

    # because the readme calls run_until_complete we need to run
    # in nested mode as the loop is already running
    import nest_asyncio
    nest_asyncio.apply()

    # can't use exec() as it doesn't set __name__ to __main__
    imp.load_module('__main__', code, '', (".py", "r", imp.PY_SOURCE))
