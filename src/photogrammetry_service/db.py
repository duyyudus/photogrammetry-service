from enum import Enum

from bson.objectid import ObjectId
from flask import Flask
from flask_pymongo import PyMongo
from pymongo.results import DeleteResult, UpdateResult

LATEST_TASK_ID_KEY = 'latest_task_id'
TASK_ID_KEY = 'task_id'
TASK_STEP_KEY = 'step'
TASK_INPUT_KEY = 'input_dir'
TASK_OUTPUT_KEY = 'output_dir'


class Step(Enum):
    NOT_STARTED = 'NOT_STARTED'
    RAW_PROCESSING = 'RAW_PROCESSING'
    COLOR_CORRECTION = 'COLOR_CORRECTION'
    PHOTO_ALIGNMENT = 'PHOTO_ALIGNMENT'
    MESH_CONSTRUCTION = 'MESH_CONSTRUCTION'
    COMPLETED = 'COMPLETED'


class DB(object):
    """Database."""

    def __init__(self, server: Flask):
        super(DB, self).__init__()
        self._mongo = PyMongo(server)
        self._server = server

    def add_task(self, task: dict) -> ObjectId:
        res = self._mongo.db.tasks.insert_one(task)

        if self._mongo.db.state.find_one():
            self._mongo.db.state.update_one({}, {'$set': {LATEST_TASK_ID_KEY: task['task_id']}})
        else:
            self._mongo.db.state.insert_one({LATEST_TASK_ID_KEY: task['task_id']})
        return res

    def get_latest_task_id(self) -> int:
        state = self._mongo.db.state.find_one()
        if state:
            tid = state[LATEST_TASK_ID_KEY] if LATEST_TASK_ID_KEY in state else 0
        else:
            tid = 0
        return tid

    def get_task(self, task_id: int) -> dict:
        task = self._mongo.db.tasks.find_one({TASK_ID_KEY: task_id})
        self._server.logger.debug(task)
        if task:
            task.pop('_id')
        return task

    def update_task(self, task_data: dict) -> UpdateResult:
        res = self._mongo.db.tasks.update_one(
            {TASK_ID_KEY: task_data[TASK_ID_KEY]}, {'$set': task_data}
        )
        return res

    def delete_task(self, task_id: int) -> DeleteResult:
        res = self._mongo.db.tasks.delete_one({TASK_ID_KEY: task_id})
        return res

    def ls_tasks(self) -> list:
        tasks = []
        for t in self._mongo.db.tasks.find():
            t.pop('_id')
            tasks.append(t)
        return tasks
