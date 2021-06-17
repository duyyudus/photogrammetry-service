import time
from enum import Enum
import logging
from logging.config import dictConfig
from types import ModuleType
from typing import Any, Tuple

from flask import Flask

from .db import DB
from .task import TASK_ID_KEY


class Status(Enum):
    SUCCESS = 'success'
    ERROR = 'error'


class DatabaseAdapter(object):
    """
    Manage photogrammetry tasks.

    All API-related methods return format: `(status: Status, data: Any, message: str)`

    """

    def __init__(self, server: Flask, db: DB):
        super(DatabaseAdapter, self).__init__()
        self._server = server
        self._db = db
        self._tasks = []

    def _sync_task(self):
        status, self._tasks, message = self.ls_tasks()

    def get_latest_task_id(self) -> int:
        return self._db.get_latest_task_id()

    def add_task(self, task_data: dict) -> Tuple[Status, None, str]:
        message = f'Added task: {task_data[TASK_ID_KEY]}'
        status = Status.SUCCESS.value
        try:
            self._db.add_task(task_data)
        except Exception as e:
            message = str(e)
            status = Status.ERROR.value
        return status, None, message

    def get_task(self, task_id: int) -> Tuple[Status, dict, str]:
        message = 'Returned task data'
        status = Status.SUCCESS.value
        task_data = {}
        try:
            task_data = self._db.get_task(task_id)
        except Exception as e:
            message = str(e)
            status = Status.ERROR.value
        return status, task_data, message

    def update_task(self, task_data: dict) -> Tuple[Status, None, str]:
        message = 'Updated task'
        status = Status.SUCCESS.value
        try:
            self._db.update_task(task_data)
        except Exception as e:
            message = str(e)
            status = Status.ERROR.value
        return status, None, message

    def delete_task(self, task_id: int) -> Tuple[Status, None, str]:
        message = 'Deleted task'
        status = Status.SUCCESS.value
        try:
            self._db.delete_task(task_id)
        except Exception as e:
            message = str(e)
            status = Status.ERROR.value
        return status, None, message

    def ls_tasks(self) -> Tuple[Status, list, str]:
        """List tasks from database"""

        message = 'Returned task list'
        status = Status.SUCCESS.value
        tasks = []
        try:
            tasks = self._db.ls_tasks()
        except Exception as e:
            message = str(e)
            status = Status.ERROR.value
        return status, tasks, message


class Coordinator(object):
    """Task coordinator."""

    def __init__(self, cfg: ModuleType):
        super(Coordinator, self).__init__()
        self._mongo_uri = cfg.MONGO_URI
        self.setup_logger(cfg)

    def setup_logger(self, cfg: ModuleType):
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
                        'stream': 'ext://sys.stdout',
                        'formatter': 'default',
                    },
                    'file_handler': {
                        'level': cfg.LOG_LEVEL,
                        'formatter': 'default',
                        'class': 'logging.FileHandler',
                        'filename': cfg.COORDINATOR_LOG,
                        'mode': 'w',
                    },
                },
                'root': {
                    'level': cfg.LOG_LEVEL,
                    'handlers': ['console_handler', 'file_handler'],
                },
            }
        )
        self.logger = logging.getLogger()

    def run(self):
        self.logger.info('Running Task Coordinator...')
        while 1:
            time.sleep(2)
