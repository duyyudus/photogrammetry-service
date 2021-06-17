import importlib.util
from pathlib import Path

from photogrammetry_service.worker import (
    color_correction_job,
    dng_conversion_job,
    mesh_construction_job,
    photo_alignment_job,
    setup_logger,
)

spec = importlib.util.spec_from_file_location(
    'config', Path(__file__).parent.joinpath('config.py').as_posix()
)
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)

setup_logger(cfg)
