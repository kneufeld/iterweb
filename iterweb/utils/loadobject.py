import importlib

def load_object(name):
    if not isinstance(name, str):
        return name

    mod_name, obj_name = name.rsplit('.', 1)
    module = importlib.import_module(mod_name)

    return getattr(module, obj_name)
