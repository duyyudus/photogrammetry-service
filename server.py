from photogrammetry_service import create_server
import os.path as osp

cfg = osp.join(osp.dirname(__file__), 'config.py')

server = create_server(cfg)
