import logging
import pprint
import time
from enum import Enum
from logging.config import dictConfig
from types import ModuleType
from typing import Any, Tuple

from pathlib import Path
from photogrammetry_service import img_util

from . import worker
from .db import DB
from .task import (
    CC_BLUR_TIFF,
    CUR_STEP_IN_PROGRESS_KEY,
    STEP_METADATA,
    TASK_ID_KEY,
    TASK_STEP_KEY,
    StepIndex,
    Task,
)


class Status(Enum):
    SUCCESS = 'success'
    ERROR = 'error'


class DatabaseAdapter(object):
    """
    Manage photogrammetry tasks.

    All API-related methods return format: `(status: Status, data: Any, message: str)`

    """

    def __init__(self, db: DB):
        super(DatabaseAdapter, self).__init__()
        self._db = db

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

    def restart_task(self, task_id: int, all_tasks: bool = False) -> Tuple[Status, None, str]:
        """Update DB to trigger tasks re-processing"""

        message = 'Requested to process task'
        status = Status.SUCCESS.value

        try:
            if all_tasks:
                tasks = self._db.ls_tasks()
            else:
                tasks = [self._db.get_task(task_id)]

            for task_data in tasks:
                task_data[TASK_STEP_KEY] = StepIndex.NOT_STARTED.value
                task_data[CUR_STEP_IN_PROGRESS_KEY] = False
                self._db.update_task(task_data)
        except Exception as e:
            message = str(e)
            status = Status.ERROR.value
        return status, None, message


class Coordinator(object):
    """
    Task coordinator.

    Monitor state of all tasks in database and send processing request to `worker`
    """

    def __init__(self, cfg: ModuleType):
        super(Coordinator, self).__init__()
        self._mongo_uri = cfg.MONGO_URI
        self._db = DB(self._mongo_uri)
        self._ext_tools: dict = cfg.EXT_TOOLS
        self._template_files: dict = cfg.TEMPLATE_FILES
        self.setup_logger(cfg)

    def setup_logger(self, cfg: ModuleType):
        Path(cfg.COORDINATOR_LOG).parent.mkdir(parents=True, exist_ok=True)
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

    def run(self, interval: float):
        """
        Coordinating loop:
            - Get list of tasks from DB
            - For current step of each task
                * If step is in progress, do further check
                    - If finished, update task data to DB ( new current step value, no longer in progress )
                    - Otherwise, skip
                * If step is NOT in progress
                    - Request `worker` to process it
                    - And update task data in DB ( mark as in progress )
        """
        self.logger.info('Running Task Coordinator...\n')

        color_swatch_cache = {}
        while 1:
            self.logger.debug('START coordinating tasks:')
            tasks = self._db.ls_tasks()
            self.logger.debug(pprint.pformat(tasks))

            for task_data in tasks:
                task = Task(task_data, self.logger, self._ext_tools, self._template_files)
                task_id = task_data[TASK_ID_KEY]

                if task.cur_step.step_id == StepIndex.COMPLETED.value:
                    continue

                if task_data[CUR_STEP_IN_PROGRESS_KEY]:
                    if task.cur_step.is_finished:
                        task_data[CUR_STEP_IN_PROGRESS_KEY] = False
                        if task.cur_step.step_id < StepIndex.COMPLETED.value:
                            task_data[TASK_STEP_KEY] += 1
                        self._db.update_task(task_data)
                        self.logger.info(
                            f'Step {STEP_METADATA[task.cur_step.step_id]["name"]} is finished'
                        )
                else:
                    sent_job = 0

                    if task.cur_step.is_finished:
                        if task.cur_step.step_id < StepIndex.COMPLETED.value:
                            task_data[TASK_STEP_KEY] += 1
                        self._db.update_task(task_data)
                        self.logger.info(
                            f'Step {STEP_METADATA[task.cur_step.step_id]["name"]} is finished'
                        )

                    elif task.cur_step.step_id == StepIndex.NOT_STARTED.value:
                        worker.init_task_job.send(task_data)
                        sent_job = 1
                        self.logger.info(f'Sent init_task_job, task: {task_id}')

                    elif task.cur_step.step_id == StepIndex.DNG_CONVERSION.value:
                        for image_name in task.cur_step.ls_input_images():
                            worker.dng_conversion_job.send(task_data, image_name)
                            sent_job = 1
                            self.logger.info(
                                f'Sent dng_conversion_job, task: {task_id}, image: {image_name}'
                            )

                    elif task.cur_step.step_id == StepIndex.COLOR_CORRECTION.value:
                        # if task.cur_step.step_id not in color_swatch_cache:
                        #     swatch = img_util.compute_swatch(task.cache_dir.joinpath(CC_BLUR_TIFF))
                        #     color_swatch_cache[task.task_id] = swatch.tolist()
                        # for image_name in task.cur_step.ls_input_images():
                        #     worker.color_correction_job.send(
                        #         task_data, image_name, color_swatch_cache[task.task_id]
                        #     )
                        #     sent_job = 1
                        #     self.logger.info(
                        #         f'Sent color_correction_job, task: {task_id}, image: {image_name}'
                        #     )

                        worker.color_correction_single_job.send(task_data)
                        sent_job = 1
                        self.logger.info(f'Sent color_correction_single_job, task: {task_id}')

                    elif task.cur_step.step_id == StepIndex.PREPARE_RC.value:
                        worker.prepare_rc_job.send(task_data)
                        sent_job = 1
                        self.logger.info(f'Sent prepare_rc_job, task: {task_id}')

                    elif task.cur_step.step_id == StepIndex.MESH_CONSTRUCTION.value:
                        worker.mesh_construction_job.send(task_data)
                        sent_job = 1
                        self.logger.info(f'Sent mesh_construction_job, task: {task_id}')

                    if (
                        StepIndex.NOT_STARTED.value
                        <= task.cur_step.step_id
                        <= StepIndex.MESH_CONSTRUCTION.value
                    ) and sent_job:
                        task_data[CUR_STEP_IN_PROGRESS_KEY] = True
                        self._db.update_task(task_data)

                    if (
                        task.cur_step.step_id > StepIndex.COLOR_CORRECTION.value
                        and task.task_id in color_swatch_cache
                    ):
                        color_swatch_cache.pop(task.task_id)

            self.logger.debug('DONE')
            self.logger.debug('')
            time.sleep(interval)
