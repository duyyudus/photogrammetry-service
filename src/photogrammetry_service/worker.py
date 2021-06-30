from importlib.machinery import ModuleSpec
import logging
from types import ModuleType

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from .task import Task

LOGGER = None
EXT_TOOLS = None
TEMPLATE_FILES = None

redis_broker = RedisBroker(host="localhost", port=6379)
dramatiq.set_broker(redis_broker)


def _setup_logger(cfg: ModuleType):
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


def _load_ext_tools(cfg: ModuleType):
    global EXT_TOOLS

    EXT_TOOLS = cfg.EXT_TOOLS


def _load_template_files(cfg: ModuleType):
    global TEMPLATE_FILES

    TEMPLATE_FILES = cfg.TEMPLATE_FILES


def setup_worker(cfg: ModuleType):
    _setup_logger(cfg)
    _load_ext_tools(cfg)
    _load_template_files(cfg)


@dramatiq.actor
def init_task_job(task_data: dict):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process()


@dramatiq.actor
def dng_conversion_job(task_data: dict, image_name: str):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process_image(image_name)


@dramatiq.actor
def color_correction_job(task_data: dict, image_name: str):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process_image(image_name)


@dramatiq.actor
def photo_alignment_job(task_data: dict):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process()


@dramatiq.actor
def mesh_construction_job(task_data: dict):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process()
