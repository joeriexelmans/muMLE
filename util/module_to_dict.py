# Based on: https://stackoverflow.com/a/46263657
def module_to_dict(module):
    context = {}
    for name in dir(module):
        # this will filter out 'private' functions, as well as __builtins__, __name__, __package__, etc.:
        if not name.startswith('_'):
            context[name] = getattr(module, name)
    return context