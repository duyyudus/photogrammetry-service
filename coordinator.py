import importlib.util
from pathlib import Path

from photogrammetry_service.task_coordinator import Coordinator

spec = importlib.util.spec_from_file_location(
    'config', Path(__file__).parent.joinpath('config.py').as_posix()
)
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)

coordinator = Coordinator(cfg)
coordinator.run()
