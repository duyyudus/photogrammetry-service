from genericpath import exists
import os
import os.path as osp
from logging.config import dictConfig
from typing import Union

from flask import Flask
from . import api


class ServerConfigNotFound(Exception):
    pass


def create_server(cfg: Union[str, dict]) -> Flask:

    app = Flask(__name__)

    if isinstance(cfg, str):
        if osp.exists(cfg):
            app.config.from_pyfile(cfg, silent=True)
        else:
            raise ServerConfigNotFound()
    elif isinstance(cfg, dict):
        app.config.from_mapping(cfg)
    else:
        raise ServerConfigNotFound()

    # Setup logger
    os.makedirs(app.config['LOG_DIR'], exist_ok=1)

    dictConfig(
        {
            'version': 1,
            'formatters': {
                'default': {
                    'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                }
            },
            'handlers': {
                'console_handler': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://flask.logging.wsgi_errors_stream',
                    'formatter': 'default',
                },
                'file_handler': {
                    'level': 'INFO',
                    'formatter': 'default',
                    'class': 'logging.FileHandler',
                    'filename': app.config['SERVER_LOG'],
                    'mode': 'w',
                },
            },
            'root': {'level': 'INFO', 'handlers': ['console_handler', 'file_handler']},
        }
    )

    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    api.route_api(app)

    return app
