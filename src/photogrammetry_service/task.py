import re
import shutil
import time
from abc import ABC, abstractmethod
from enum import Enum
from logging import Logger
from pathlib import Path
from typing import Any, List, Optional, Pattern, Tuple, Union

from . import ext_tool_adaptor as ext_tool
from . import img_util

LATEST_TASK_ID_KEY = 'latest_task_id'
TASK_ID_KEY = 'task_id'
TASK_STEP_KEY = 'step'
TASK_LOCATION_KEY = 'task_location'
CUR_STEP_IN_PROGRESS_KEY = 'cur_step_in_progress'


class StepIndex(Enum):
    NOT_STARTED = 0
    DNG_CONVERSION = 1
    COLOR_CORRECTION = 2
    PHOTO_ALIGNMENT = 3
    MESH_CONSTRUCTION = 4
    COMPLETED = 5


class TaskResource(Enum):
    CACHE = 'cache'
    RAW = '1_RAW'
    DNG = '2_DNG'
    COLOR_CORRECTED = '3_COLOR_CORRECTED'
    MESH_CONSTRUCTION = '4_MESH_CONSTRUCTION'
    FINAL_RESULT = '5_FINAL_RESULT'


IMAGE_PATTERN = r'\w*\d*'
STEP_METADATA = {
    StepIndex.NOT_STARTED.value: {
        'name': 'Not Started',
        'input_folder': None,
        'input_image_ext': None,
        'output_folder': TaskResource.RAW.value,
        'output_image_ext': 'ARW',
    },
    StepIndex.DNG_CONVERSION.value: {
        'name': 'DNG Conversion',
        'input_folder': TaskResource.RAW.value,
        'input_image_ext': 'ARW',
        'output_folder': TaskResource.DNG.value,
        'output_image_ext': 'dng',
    },
    StepIndex.COLOR_CORRECTION.value: {
        'name': 'Color Correction',
        'input_folder': TaskResource.DNG.value,
        'input_image_ext': 'dng',
        'output_folder': TaskResource.COLOR_CORRECTED.value,
        'output_image_ext': 'jpg',
    },
    StepIndex.PHOTO_ALIGNMENT.value: {
        'name': 'Photo Alignment',
        'input_folder': TaskResource.COLOR_CORRECTED.value,
        'input_image_ext': 'jpg',
        'output_folder': TaskResource.MESH_CONSTRUCTION.value,
        'output_image_ext': None,
    },
    StepIndex.MESH_CONSTRUCTION.value: {
        'name': 'Mesh Construction',
        'input_folder': TaskResource.MESH_CONSTRUCTION.value,
        'input_image_ext': None,
        'output_folder': TaskResource.FINAL_RESULT.value,
        'output_image_ext': None,
    },
    StepIndex.COMPLETED.value: {
        'name': 'Completed',
        'input_folder': TaskResource.FINAL_RESULT.value,
        'input_image_ext': None,
        'output_folder': None,
        'output_image_ext': None,
    },
}


class Step(ABC):
    """Base class for `Step` in a `Task`."""

    def __init__(self, step_id: StepIndex, task: 'Task'):
        super(Step, self).__init__()
        self._step_id = step_id
        self._task = task

    @property
    def step_id(self) -> int:
        return self._step_id

    @property
    def task(self) -> 'Task':
        return self._task

    @property
    def task_location(self) -> Path:
        return self._task.task_location

    @property
    def logger(self) -> Logger:
        return self._task.logger

    @property
    def input_dir(self) -> Optional[Path]:
        """The path of directoty that contain input data"""

        input_folder = STEP_METADATA[self._step_id]['input_folder']
        if input_folder:
            p = self.task_location.joinpath(input_folder)
        else:
            p = None
        return p

    @property
    def output_dir(self) -> Optional[Path]:
        """The path of directoty that contain output data"""

        output_folder = STEP_METADATA[self._step_id]['output_folder']
        if output_folder:
            p = self.task_location.joinpath(output_folder)
        else:
            p = None
        return p

    def ls_input_images(self, image_name_only=True) -> List[Union[Path, str]]:
        """List of images in input data folder, if any"""

        images = []
        if not self.input_dir.exists():
            return images

        pattern = self.full_image_file_name(
            IMAGE_PATTERN, STEP_METADATA[self.step_id]['input_image_ext']
        )
        if pattern:
            images = [
                p.stem if image_name_only else p
                for p in self.input_dir.iterdir()
                if re.match(pattern, p.name)
            ]
        return images

    def ls_output_images(self, image_name_only=True) -> List[Union[Path, str]]:
        """List of images in output data folder, if any"""

        images = []
        if not self.output_dir.exists():
            return images

        pattern = self.full_image_file_name(
            IMAGE_PATTERN, STEP_METADATA[self.step_id]['output_image_ext']
        )
        if pattern:
            images = [
                p.stem if image_name_only else p
                for p in self.output_dir.iterdir()
                if re.match(pattern, p.name)
            ]
        return images

    def full_image_file_name(self, *args) -> str:
        """Full image file names from parts"""
        return f'{args[0]}.{args[1]}'

    @property
    @abstractmethod
    def is_finished(self) -> bool:
        """Check if this `Step` is finished"""
        return

    @abstractmethod
    def _process_image(self, input_image: Path, output_image: Path) -> bool:
        """Process a single atomic element (e.g. individual images) of this `Step`

        Apply for `Step`s that output multiple images
        """
        return

    def process_image(self, image_name: str) -> bool:
        """Wrap `self._process_image()` with interpreted
        input and output image path from `image_name`

        For instance, if full image file name is `IMG01234.ARW`, then `image_name` is `IMG01234`
        """

        if not (self.input_dir and self.output_dir):
            return

        in_img_path = self.input_dir.joinpath(
            self.full_image_file_name(image_name, STEP_METADATA[self.step_id]['input_image_ext'])
        )
        out_img_path = self.output_dir.joinpath(
            self.full_image_file_name(image_name, STEP_METADATA[self.step_id]['output_image_ext'])
        )
        return self._process_image(in_img_path, out_img_path)

    @abstractmethod
    def _process(self) -> bool:
        """Process this `Step` as a whole

        Apply for `Step`s that does not output multiple images
        """
        return

    def process(self) -> bool:
        """Wraps `self._process()`"""

        return self._process()


##########################################################################################
###############################################################################

# TODO WIP: implement different types of Step here


class NotStartedStep(Step):
    def __init__(self, *args):
        super(NotStartedStep, self).__init__(*args)

    @property
    def is_finished(self) -> bool:
        black = self.task.cache_dir.joinpath('black.dng')
        cc_blur = self.task.cache_dir.joinpath('color_checker_blur.tiff')
        return black.exists() and cc_blur.exists()

    def _process_image(self, input_image: Path, output_image: Path) -> bool:
        return

    def _process(self) -> bool:
        """Create initial cache files"""
        succeed = 1
        done = 0
        try:
            while not done:
                time.sleep(2)

                # Copy black image from template to cache folder
                src_black = Path(self.task.template_files['BLACK'])
                tg_black = self.task.cache_dir.joinpath('black.dng')
                if src_black.exists() and not tg_black.exists():
                    tg_black.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src_black, tg_black)
                    self.logger.info(f'Cloned black image: {tg_black}')

                # Convert user's color checker raw image to dng
                raw_cc = self.task.cache_dir.joinpath('color_checker.ARW')
                if raw_cc.exists():
                    ext_tool.run_dng_conversion(
                        raw_cc, self.task.cache_dir, Path(self.task.ext_tools['DNG_CONVERTER'])
                    )
                    self.logger.info(f'Converted {raw_cc.name} to DNG')
                else:
                    self.logger.warning(
                        f'{raw_cc.name} not found, please put it in {self.task.cache_dir}'
                    )
                    continue

                # Blur color checker and save as tiff
                dng_cc = self.task.cache_dir.joinpath('color_checker.dng')
                png_cc = self.task.cache_dir.joinpath('color_checker.png')
                png_cc_blur = self.task.cache_dir.joinpath('color_checker_blur.png')
                tif_cc_blur = self.task.cache_dir.joinpath('color_checker_blur.tiff')
                if dng_cc.exists():
                    img_util.dng_to_png(dng_cc, png_cc)
                    self.logger.info(f'Converted {dng_cc.name} to PNG')

                    img_util.blur(png_cc, png_cc_blur)
                    self.logger.info(f'Generated blur {png_cc_blur.name} from {png_cc.name}')

                    img_util.png_to_tif(png_cc_blur, tif_cc_blur)
                    self.logger.info(f'Converted {png_cc_blur.name} to TIFF')

                    done = 1
                    self.logger.info(f'Finished blurring process: {tif_cc_blur}')
                else:
                    self.logger.warning(f'{dng_cc.name} not found, failed to do blurring')
                    continue

        except Exception as e:
            self.logger.error(f'Init task error :: {str(e)}')
            succeed = 0
        return succeed


class DngConversionStep(Step):
    def __init__(self, *args):
        super(DngConversionStep, self).__init__(*args)

    @property
    def is_finished(self) -> bool:
        return len(self.ls_input_images()) == len(self.ls_output_images())

    def _process_image(self, input_image: Path, output_image: Path) -> bool:
        succeed = 1
        try:
            output_image.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(input_image, output_image)
            self.logger.debug(f'Converted to DNG: {output_image}')
        except Exception as e:
            self.logger.error(f'DNG conversion error: {input_image} :: {str(e)}')
            succeed = 0
        return succeed

    def _process(self) -> bool:
        return


class ColorCorrectionStep(Step):
    def __init__(self, *args):
        super(ColorCorrectionStep, self).__init__(*args)

    @property
    def is_finished(self) -> bool:
        return len(self.ls_input_images()) == len(self.ls_output_images())

    def _process_image(self, input_image: Path, output_image: Path) -> bool:
        succeed = 1
        try:
            output_image.parent.mkdir(parents=True, exist_ok=1)
            shutil.copyfile(input_image, output_image)
            self.logger.debug(f'Color corrected: {output_image}')
        except Exception as e:
            self.logger.error(f'Color correction error: {input_image} :: {str(e)}')
            succeed = 0
        return succeed

    def _process(self) -> bool:
        return


class PhotoAlignmentStep(Step):
    def __init__(self, *args):
        super(PhotoAlignmentStep, self).__init__(*args)

    @property
    def dummy_file(self) -> Path:
        return self.output_dir.joinpath('PHOTO_ALIGNMENT_DUMMY')

    @property
    def is_finished(self) -> bool:
        return self.dummy_file.exists()

    def _process_image(self, input_image: Path, output_image: Path) -> bool:
        return

    def _process(self) -> bool:
        succeed = 1
        try:
            ext_tool.run_photo_alignment(self.input_dir, self.output_dir, self.dummy_file)
            self.logger.debug(f'Finished photo alignment: {self.output_dir}')
        except Exception as e:
            self.logger.error(f'Photo alignment error :: {str(e)}')
            succeed = 0
        return succeed


class MeshConstructionStep(Step):
    def __init__(self, *args):
        super(MeshConstructionStep, self).__init__(*args)

    @property
    def dummy_file(self) -> Path:
        return self.output_dir.joinpath('MESH_CONSTRUCTION_DUMMY')

    @property
    def is_finished(self) -> bool:
        return self.dummy_file.exists()

    def _process_image(self, input_image: Path, output_image: Path) -> bool:
        return

    def _process(self) -> bool:
        succeed = 1
        try:
            ext_tool.run_mesh_construction(self.input_dir, self.output_dir, self.dummy_file)
            self.logger.debug(f'Finished mesh construction: {self.output_dir}')
        except Exception as e:
            self.logger.error(f'Mesh construction error :: {str(e)}')
            succeed = 0
        return succeed


class CompletedStep(Step):
    def __init__(self, *args):
        super(CompletedStep, self).__init__(*args)

    @property
    def is_finished(self) -> bool:
        return True

    def _process_image(self, input_image: Path, output_image: Path) -> bool:
        return

    def _process(self) -> bool:
        return


###############################################################################
##########################################################################################

STEP_CLASS_MAP = {
    StepIndex.NOT_STARTED.value: NotStartedStep,
    StepIndex.DNG_CONVERSION.value: DngConversionStep,
    StepIndex.COLOR_CORRECTION.value: ColorCorrectionStep,
    StepIndex.PHOTO_ALIGNMENT.value: PhotoAlignmentStep,
    StepIndex.MESH_CONSTRUCTION.value: MeshConstructionStep,
    StepIndex.COMPLETED.value: CompletedStep,
}


class Task(object):
    """A photogrammetry task."""

    def __init__(self, task_data: dict, logger: Logger, ext_tools: dict, template_files: dict):
        super(Task, self).__init__()
        self._task_data = task_data
        self._logger = logger
        self._ext_tools = ext_tools
        self._template_files = template_files

    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def ext_tools(self) -> dict:
        return self._ext_tools

    @property
    def template_files(self) -> dict:
        return self._template_files

    @property
    def task_data(self) -> dict:
        """
        {
            "task_id": int,
            "task_location": str, # E.g. "/path/to/some/folder"
            "step": int,
            "cur_step_pending": bool,
        }
        """
        return self._task_data

    @property
    def task_location(self) -> Path:
        return Path(self._task_data[TASK_LOCATION_KEY])

    @property
    def cache_dir(self) -> Path:
        return self.task_location.joinpath(TaskResource.CACHE.value)

    @property
    def cur_step(self) -> Step:
        """The current step."""
        step_id = self._task_data[TASK_STEP_KEY]
        return STEP_CLASS_MAP[step_id](step_id, self)
