import json

from flask import Flask, request

from .db import DB, TASK_ID_KEY, TASK_STEP_KEY, TASK_INPUT_KEY, TASK_OUTPUT_KEY, Step
from .task_manager import TaskManager

SUCCESS = 'success'
ERROR = 'error'


class ApiHandler(object):
    """Handle public APIs."""

    def __init__(self, server: Flask, task_manager: TaskManager, db: DB):
        super(ApiHandler, self).__init__()
        self._server = server
        self._task_manager = task_manager
        self._db = db

    def register_api(self):
        @self._server.route('/about')
        def about():
            return {'status': SUCCESS, 'data': {}, 'message': self._server.config['ABOUT']}

        @self._server.route('/add_task')
        def add_task():
            input_dir = request.args.get(TASK_INPUT_KEY, type=str)
            output_dir = request.args.get(TASK_OUTPUT_KEY, type=str)
            self._server.logger.debug('Added task:')
            self._server.logger.debug(f'--Input dir: {input_dir}')
            self._server.logger.debug(f'--Output dir: {output_dir}')

            message = ''
            status = ''
            if input_dir and output_dir:
                new_task_id = self._db.get_latest_task_id() + 1

                # TODO: add_task logic here
                # ...

                self._db.add_task(
                    {
                        TASK_ID_KEY: new_task_id,
                        TASK_OUTPUT_KEY: input_dir,
                        TASK_INPUT_KEY: output_dir,
                        TASK_STEP_KEY: Step.NOT_STARTED.value,
                    }
                )

                message = f'Added task: {new_task_id}'
                status = SUCCESS
            else:
                message = f'Please provide {"input dir" if not input_dir else "output dir"}'
                status = ERROR

            res = {'status': status, 'data': {}, 'message': message}
            return res

        @self._server.route('/get_task')
        def get_task():
            """Return task data from task ID"""
            task_id = request.args.get('task_id', type=int)
            self._server.logger.debug(f'Get task: {task_id}')

            message = 'Returned task data'
            status = SUCCESS

            task = {}
            if task_id:
                # TODO: get_task logic here
                # ...
                task = self._db.get_task(task_id)
            else:
                message = 'Please provide task ID'
                status = ERROR

            res = {'status': status, 'data': task, 'message': message}
            return res

        @self._server.route('/update_task')
        def update_task():
            """Update task"""
            task_data = request.args.get('task_data', type=str)
            self._server.logger.debug('Update task:')
            self._server.logger.debug(f'--Task data: {task_data}')

            if task_data:
                # TODO: update_task logic here
                # ...

                self._db.update_task(json.loads(task_data))

                message = 'Updated task'
                status = SUCCESS
            else:
                message = 'Please provide task ID'
                status = ERROR

            res = {'status': status, 'data': {}, 'message': message}
            return res

        @self._server.route('/delete_task')
        def delete_task():
            """Delete task"""
            task_id = request.args.get('task_id', type=int)
            self._server.logger.debug(f'Delete task: {task_id}')

            if task_id:
                # TODO: delete_task logic here
                # ...

                self._db.delete_task(task_id)

                message = 'Deleted task'
                status = SUCCESS
            if not task_id:
                message = 'Please provide task ID'
                status = ERROR

            res = {'status': status, 'data': {}, 'message': message}
            return res

        @self._server.route('/ls_tasks')
        def ls_tasks():
            """Return a list of task IDs"""
            message = 'Returned task list'
            status = SUCCESS
            tasks = self._db.ls_tasks()
            res = {'status': status, 'data': {'tasks': tasks}, 'message': message}
            return res
