import os.path as osp

ABOUT = 'Photogrammetry Service'
LOG_DIR = f'{osp.dirname(osp.abspath(__file__))}/.pslog'
SERVER_LOG = f'{LOG_DIR}/server.log'
WORKER_LOG = f'{LOG_DIR}/worker.log'
COORDINATOR_LOG = f'{LOG_DIR}/coordinator.log'
LOG_LEVEL = 'DEBUG'
MONGO_URI = 'mongodb://localhost:27017/photogrammetry_service'
