from contextlib import contextmanager


@contextmanager
def attribute(obj, name, value):
    original = getattr(obj, name)
    try:
        setattr(obj, name, value)
        yield
    finally:
        setattr(obj, name, original)


def maybe_remove(d, *keys):
    for key in keys:
        try:
            del d[key]
        except KeyError:
            pass

