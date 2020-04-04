import inspect
import asyncio
import importlib
from functools import partial

from . import DropItem, DropItemError

import logging
logger = logging.getLogger(__name__)

def load_object(name):
    if not isinstance(name, str):
        return name

    mod_name, obj_name = name.rsplit('.', 1)
    module = importlib.import_module(mod_name)

    return getattr(module, obj_name)


class Pipeline:

    def __init__(self, stages):
        self.stages = self.build_pipeline(stages)

    @classmethod
    def build_pipeline(cls, stages):
        """
        if pipeline members are strings then load them
        else assure that they're coroutines or class with process_item
        """
        if not stages:
            return []

        ret = []

        for stage in stages:
            if isinstance(stage, str):
                stage = load_object(stage)

            if inspect.isclass(stage):
                assert asyncio.iscoroutinefunction(getattr(stage, 'process_item'))
                stage = partial(stage().process_item) # instantiate class
            else:
                assert asyncio.iscoroutinefunction(stage)

            ret.append(stage)

        return ret

    async def process(self, spider, response, item):
        """
        pass item through provided pipeline, a pipeline stage
        can return the item, or raise DropItem
        """
        if item is None:
            return None

        for stage in self.stages:
            try:
                # logger.debug(stage)
                item = await stage(spider, response, item)

            except DropItem as e:
                # THINK should we be logging or the called function?
                logger.debug("%s: dropping item: %s", stage.__class__.__name__, e)
                return None

            except DropItemError as e:
                # THINK should we be logging or the called function?
                logger.error("%s: dropping item: %s", stage.__class__.__name__, e)
                return None

            except Exception as e:
                # THINK should we really be catching this?
                logger.error("%s: exception: %s", stage.__class__.__name__, e)
                logger.exception(e)
                return None

        return item
