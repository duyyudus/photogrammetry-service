from bson.objectid import ObjectId
from flask import Flask
from flask_pymongo import PyMongo
from pymongo.results import DeleteResult, UpdateResult

from .task import LATEST_TASK_ID_KEY, TASK_ID_KEY


class DB(object):
    """Database."""

    def __init__(self, server: Flask):
        super(DB, self).__init__()
        self._mongo = PyMongo(server)
        self._server = server

    def add_task(self, task_data: dict) -> ObjectId:
        res = self._mongo.db.tasks.insert_one(task_data)

        if self._mongo.db.state.find_one():
            self._mongo.db.state.update_one(
                {}, {'$set': {LATEST_TASK_ID_KEY: task_data['task_id']}}
            )
        else:
            self._mongo.db.state.insert_one({LATEST_TASK_ID_KEY: task_data['task_id']})
        return res

    def get_latest_task_id(self) -> int:
        state = self._mongo.db.state.find_one()
        if state:
            tid = state[LATEST_TASK_ID_KEY] if LATEST_TASK_ID_KEY in state else -1
        else:
            tid = -1
        return tid

    def get_task(self, task_id: int) -> dict:
        task_data = self._mongo.db.tasks.find_one({TASK_ID_KEY: task_id})
        self._server.logger.debug(task_data)
        if task_data:
            task_data.pop('_id')
        return task_data

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
