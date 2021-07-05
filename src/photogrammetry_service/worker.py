import logging
from types import ModuleType
from pathlib import Path
import dramatiq
from dramatiq.brokers.redis import RedisBroker

from .img_util import ColourCheckerSwatchesData
from .task import Task

LOGGER = None
EXT_TOOLS = None
TEMPLATE_FILES = None

redis_broker = RedisBroker(host="localhost", port=6379)
dramatiq.set_broker(redis_broker)


def _setup_logger(cfg: ModuleType):
    global LOGGER

    Path(cfg.WORKER_LOG).parent.mkdir(parents=True, exist_ok=True)

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


@dramatiq.actor(time_limit=48000000, max_retries=0)
def init_task_job(task_data: dict):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process()


@dramatiq.actor(time_limit=48000000, max_retries=0)
def dng_conversion_job(task_data: dict, image_name: str):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process_image(image_name)


@dramatiq.actor(time_limit=48000000, max_retries=0)
def color_correction_job(task_data: dict, image_name: str, swatch: ColourCheckerSwatchesData):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process_image(image_name, swatch)


@dramatiq.actor(time_limit=48000000, max_retries=0)
def color_correction_single_job(task_data: dict):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process()


@dramatiq.actor(time_limit=48000000, max_retries=0)
def prepare_rc_job(task_data: dict):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process()


@dramatiq.actor(time_limit=48000000, max_retries=0)
def mesh_construction_job(task_data: dict):
    task = Task(task_data, LOGGER, EXT_TOOLS, TEMPLATE_FILES)
    task.cur_step.process()
