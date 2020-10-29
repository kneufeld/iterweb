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
    """
    A pipeline is a list of functions that are called with the item
    that is emitted from Spider.parse(). The item can be modified for
    future stages or a stage can raise DropItem to stop processing.
    """

    def __init__(self, stages):
        self.stages = self.build_pipeline(stages)

        # THINK should an optional drop_callback be passed in that gets
        # called if item is dropped in pipeline? Could be the best way
        # to log that event

    @classmethod
    def build_pipeline(cls, stages):
        """
        if pipeline members are strings then load them
        else assure that they're coroutines or class with process_item
        """
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

    def stage_name(self, stage):
        if isinstance(stage, partial):
            if inspect.ismethod(stage.func):
                cls_name = stage.func.__self__.__class__.__name__
                # func_name = stage.func.__name__
                return cls_name # appending .process_item seems redundant
            else:
                return stage.func.__name__

        return stage.__class__.__name__

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
                logger.debug("%s: dropping item: %s", self.stage_name(stage), e)
                return None

            except DropItemError as e:
                # THINK should we be logging or the called function?
                logger.error("%s: dropping item: %s", self.stage_name(stage), e)
                return None

            except Exception as e:
                # THINK should we really be catching this?
                logger.error("%s: exception: %s", self.stage_name(stage), e)
                logger.exception(e)
                return None

        return item
