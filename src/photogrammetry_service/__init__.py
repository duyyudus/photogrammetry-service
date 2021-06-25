import os
import os.path as osp
from logging.config import dictConfig
from typing import Union

from flask import Flask

from .api import ApiHandler
from .db import DB
from .task_coordinator import DatabaseAdapter


class ServerConfigNotFound(Exception):
    pass


def create_server(cfg: Union[str, dict]) -> Flask:

    server = Flask(__name__)

    if isinstance(cfg, str):
        if osp.exists(cfg):
            server.config.from_pyfile(cfg, silent=True)
        else:
            raise ServerConfigNotFound()
    elif isinstance(cfg, dict):
        server.config.from_mapping(cfg)
    else:
        raise ServerConfigNotFound()

    # Setup logger
    os.makedirs(server.config['LOG_DIR'], exist_ok=1)

    dictConfig(
        {
            'version': 1,
            'formatters': {
                'default': {
                    'format': '[%(asctime)s] %(module)s.py %(levelname)s: %(message)s',
                }
            },
            'handlers': {
                'console_handler': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://flask.logging.wsgi_errors_stream',
                    'formatter': 'default',
                },
                'file_handler': {
                    'level': server.config['LOG_LEVEL'],
                    'formatter': 'default',
                    'class': 'logging.FileHandler',
                    'filename': server.config['SERVER_LOG'],
                    'mode': 'w',
                },
            },
            'root': {
                'level': server.config['LOG_LEVEL'],
                'handlers': ['console_handler', 'file_handler'],
            },
        }
    )

    db = DB(server.config['MONGO_URI'])

    db_adaptor = DatabaseAdapter(db)

    api_handler = ApiHandler(server, db_adaptor)
    api_handler.register_api()

    return server
