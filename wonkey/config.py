import os

defaults = {
    'chunk_size': 2 * 1024 * 1024,
    'upload_redirect': '',
    'upload_secret': '',
    'content_dir': './content',
}

class Config(object):
    def __init__(self):
        self.__dict__ = {k: os.environ.get(k.upper(), v) for k, v in defaults.items()}

config = Config()
config.chunk_size = int(config.chunk_size)
config.content_dir = os.path.realpath(config.content_dir)
try:
    os.makedirs(config.content_dir)
except os.error:
    if not os.path.isdir(config.content_dir):
        raise
