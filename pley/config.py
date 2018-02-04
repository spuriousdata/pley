import os
import yaml


__cfg = None


def dict_path(dct, k, default=None):
    """
    Turns dotted 'path' into dict key.
    snippet.thumbnails.default ->
        dct['snippet']['thumbnails']['default']
    """
    parts = k.split('.')
    out = dct
    for p in parts:
        try:
            out = out[p]
        except KeyError:
            return default
    return out


def init(f="~/.pley.yaml"):
    global __cfg
    with open(os.path.expanduser(f), 'r') as fp:
        __cfg = yaml.load(fp.read())


def get(k, default=None):
    if __cfg is None:
        raise Exception("Configuration not set up, must call config.init() first")
    return dict_path(__cfg, k, default)
