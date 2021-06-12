from .db import DB


class TaskManager(object):
    """Manage photogrammetry task."""

    def __init__(self, server_cfg: dict, db: DB):
        super(TaskManager, self).__init__()
        self._server_cfg = server_cfg
        self._db = db
