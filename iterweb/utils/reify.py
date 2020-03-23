# https://docs.pylonsproject.org/projects/pyramid/en/latest/_modules/pyramid/decorator.html#reify

class reify():
    """
    convert property into a variable on first call

    KN: you can override name if required (like on a functools.partial)
    this is modified from original

    class Foo():
        @reify
        def future_variable(self):
          return expensive_call()
    """
    def __init__(self, wrapped, name=None):
        self.wrapped = wrapped

        if name is None:
            from functools import update_wrapper
            update_wrapper(self, wrapped)
        else:
            self.wrapped.__name__ = name

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val
