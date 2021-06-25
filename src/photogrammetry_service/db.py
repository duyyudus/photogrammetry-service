from typing import List

from bson.objectid import ObjectId
from flask import Flask
from pymongo import MongoClient
from pymongo.results import DeleteResult, UpdateResult

from .task import (
    CUR_STEP_IN_PROGRESS_KEY,
    LATEST_TASK_ID_KEY,
    StepIndex,
    TASK_ID_KEY,
    TASK_STEP_KEY,
)


class DB(object):
    """Database."""

    def __init__(self, mongo_uri: str, server: Flask = None):
        super(DB, self).__init__()
        self._db = MongoClient(mongo_uri).photogrammetry_service
        self._server = server

    def add_task(self, task_data: dict) -> ObjectId:
        res = self._db.tasks.insert_one(task_data)

        if self._db.state.find_one():
            self._db.state.update_one({}, {'$set': {LATEST_TASK_ID_KEY: task_data['task_id']}})
        else:
            self._db.state.insert_one({LATEST_TASK_ID_KEY: task_data['task_id']})
        return res

    def get_latest_task_id(self) -> int:
        state = self._db.state.find_one()
        if state:
            tid = state[LATEST_TASK_ID_KEY] if LATEST_TASK_ID_KEY in state else -1
        else:
            tid = -1
        return tid

    def get_task(self, task_id: int) -> dict:
        task_data = self._db.tasks.find_one({TASK_ID_KEY: task_id})
        if task_data:
            task_data.pop('_id')
        return task_data

    def update_task(self, task_data: dict) -> UpdateResult:
        res = self._db.tasks.update_one({TASK_ID_KEY: task_data[TASK_ID_KEY]}, {'$set': task_data})
        return res

    def delete_task(self, task_id: int) -> DeleteResult:
        res = self._db.tasks.delete_one({TASK_ID_KEY: task_id})
        return res

    def ls_tasks(self) -> List[dict]:
        tasks = []
        for t in self._db.tasks.find():
            t.pop('_id')
            tasks.append(t)
        return tasks
