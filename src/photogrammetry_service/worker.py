import logging
from logging.config import dictConfig
from types import ModuleType

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from .task import Task

LOGGER = None

redis_broker = RedisBroker(host="localhost", port=6379)
dramatiq.set_broker(redis_broker)


def setup_logger(cfg: ModuleType):
    global LOGGER

    logger = logging.getLogger('dramatiq')
    logger.setLevel(cfg.LOG_LEVEL)

    ch = logging.StreamHandler()
    fh = logging.FileHandler(cfg.WORKER_LOG, 'w')

    formatter = logging.Formatter('[%(asctime)s] %(module)s.py %(levelname)s: %(message)s')

    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    LOGGER = logger


@dramatiq.actor
def dng_conversion_job(task_data: dict, image_name: str):
    task = Task(task_data, LOGGER)
    task.cur_step.process_image(image_name)


@dramatiq.actor
def color_correction_job(task_data: dict, image_name: str):
    task = Task(task_data, LOGGER)
    task.cur_step.process_image(image_name)


@dramatiq.actor
def photo_alignment_job(task_data: dict):
    task = Task(task_data, LOGGER)
    task.cur_step.process()


@dramatiq.actor
def mesh_construction_job(task_data: dict):
    task = Task(task_data, LOGGER)
    task.cur_step.process()
