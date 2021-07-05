import os.path as osp

ABOUT = 'Photogrammetry Service'
LOG_DIR = f'{osp.dirname(osp.abspath(__file__))}/.pslog'
SERVER_LOG = f'{LOG_DIR}/server.log'
WORKER_LOG = f'{LOG_DIR}/worker.log'
COORDINATOR_LOG = f'{LOG_DIR}/coordinator.log'
LOG_LEVEL = 'INFO'
MONGO_URI = 'mongodb://localhost:27017/'

EXT_TOOLS = {
    'DNG_CONVERTER': '/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter',
    # 'DNG_CONVERTER': f'{osp.dirname(osp.abspath(__file__))}/win_dependences/AdobeDNGConverter/AdobeDNGConverter.exe',
    'REALITY_CAPTURE': r'C:\\Program Files\\Capturing Reality\\RealityCapture\\RealityCapture.exe',
}

TEMPLATE_FILES = {
    'RC_SETTING': f'{osp.dirname(osp.abspath(__file__))}/template/rc_setting',
    'BLACK': f'{osp.dirname(osp.abspath(__file__))}/template/black.dng',
    'COLOR_CHECKER': f'{osp.dirname(osp.abspath(__file__))}/template/color_checker.dng',
}
