import json

from flask import Flask, request

from .task import (
    TASK_ID_KEY,
    TASK_LOCATION_KEY,
    TASK_STEP_KEY,
    STEP_IN_PROGRESS_KEY,
    REQUIRE_KEY,
    REQ_COLOR_CHECKER_KEY,
    REQ_RAW_IMAGE_KEY,
    StepIndex,
)
from .task_coordinator import Status, DatabaseAdapter


class ApiHandler(object):
    """Handle public APIs."""

    def __init__(self, server: Flask, db_adaptor: DatabaseAdapter):
        super(ApiHandler, self).__init__()
        self._server = server
        self._db_adaptor = db_adaptor

    def register_api(self):
        @self._server.route('/about')
        def about():
            return {
                'status': Status.SUCCESS.value,
                'data': {},
                'message': self._server.config['ABOUT'],
            }

        @self._server.route('/add_task', methods=['POST'])
        def add_task():
            task_location = request.args.get(TASK_LOCATION_KEY, type=str)
            self._server.logger.debug('Added task:')
            self._server.logger.debug(f'--Task location: {task_location}')

            if task_location:
                new_task_id = self._db_adaptor.get_latest_task_id() + 1
                task_data = {
                    TASK_ID_KEY: new_task_id,
                    TASK_LOCATION_KEY: task_location,
                    TASK_STEP_KEY: StepIndex.NOT_STARTED.value,
                    STEP_IN_PROGRESS_KEY: False,
                    REQUIRE_KEY: {
                        REQ_COLOR_CHECKER_KEY: True,
                        REQ_RAW_IMAGE_KEY: True,
                    },
                }

                status, data, message = self._db_adaptor.add_task(task_data)

            else:
                status = Status.ERROR.value
                data = {}
                message = 'Please provide task location directory'

            return {'status': status, 'data': data, 'message': message}

        @self._server.route('/get_task')
        def get_task():
            """Return task data from task ID"""
            task_id = request.args.get('task_id', type=int)
            self._server.logger.debug(f'Get task: {task_id}')

            if task_id or task_id == 0:
                status, task_data, message = self._db_adaptor.get_task(task_id)
            else:
                status = Status.ERROR.value
                task_data = {}
                message = 'Please provide task ID'

            return {'status': status, 'data': task_data, 'message': message}

        @self._server.route('/update_task', methods=['POST'])
        def update_task():
            """Update task"""
            task_data = request.args.get('task_data', type=str)
            self._server.logger.debug('Update task:')
            self._server.logger.debug(f'--Task data: {task_data}')

            if task_data:
                status, data, message = self._db_adaptor.update_task(json.loads(task_data))
            else:
                status = Status.ERROR.value
                data = {}
                message = 'Please provide task ID'

            return {'status': status, 'data': data, 'message': message}

        @self._server.route('/delete_task', methods=['POST'])
        def delete_task():
            """Delete task"""
            task_id = request.args.get('task_id', type=int)
            self._server.logger.debug(f'Delete task: {task_id}')

            if task_id or task_id == 0:
                status, data, message = self._db_adaptor.delete_task(task_id)
            else:
                status = Status.ERROR.value
                data = {}
                message = 'Please provide task ID'

            return {'status': status, 'data': data, 'message': message}

        @self._server.route('/ls_tasks')
        def ls_tasks():
            """Return a list of task IDs"""
            status, data, message = self._db_adaptor.ls_tasks()
            return {'status': status, 'data': data, 'message': message}

        @self._server.route('/restart_task', methods=['POST'])
        def restart_task():
            """Force process a specific task or all tasks"""
            task_id = request.args.get('task_id', type=int)
            all_tasks = request.args.get('all_tasks', type=bool, default=False)
            self._server.logger.debug(f'Process task: {task_id}, all tasks: {all_tasks}')

            if task_id or task_id == 0 or all_tasks:
                status, task_data, message = self._db_adaptor.restart_task(task_id, all_tasks)
            else:
                status = Status.ERROR.value
                task_data = {}
                message = 'Please provide task ID'

            return {'status': status, 'data': task_data, 'message': message}
