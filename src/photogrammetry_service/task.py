import re
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Pattern, Tuple, Union

LATEST_TASK_ID_KEY = 'latest_task_id'
TASK_ID_KEY = 'task_id'
TASK_STEP_KEY = 'step'
TASK_LOCATION_KEY = 'task_location'


class StepIndex(Enum):
    NOT_STARTED = 0
    DNG_CONVERSION = 1
    COLOR_CORRECTION = 2
    PHOTO_ALIGNMENT = 3
    MESH_CONSTRUCTION = 4
    COMPLETED = 5


class TaskResource(Enum):
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
    def task_location(self) -> Path:
        return self._task.task_location

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
    def _process_image(self, input_image: Path, output_image: Path):
        """Process a single atomic element (e.g. individual images) of this `Step`

        Apply for `Step`s that output multiple images
        """
        pass

    def process_image(self, image_name: str):
        """Wrap `self._process_image()` with interpreted
        input and output image path from `image_name`

        For instance, if full image file name is `IMG01234.ARW`, then `image_name` is `IMG01234`
        """

        if not self.input_dir:
            return

        in_img_path = self.input_dir.joinpath(
            self.full_image_file_name(image_name, STEP_METADATA[self.step_id]['input_image_ext'])
        )
        out_img_path = self.output_dir.joinpath(
            self.full_image_file_name(image_name, STEP_METADATA[self.step_id]['output_image_ext'])
        )
        return self._process_image(in_img_path, out_img_path)

    @abstractmethod
    def _process(self):
        """Process this `Step` as a whole

        Apply for `Step`s that does not output multiple images
        """
        pass

    def process(self):
        """Wraps `self._process()`"""
        pass


# TODO: implement different types of Step here


class Task(object):
    """A photogrammetry task.

    `self._task_data` format::

        {
            "task_id": int,
            "task_location": str, # E.g. "/path/to/some/folder"
            "step": int,
        }

    """

    def __init__(self, task_data: dict):
        super(Task, self).__init__()
        self._task_data = task_data
        self._cur_step_id = 0

        self.sync_cur_step()

        self._steps = {
            StepIndex.NOT_STARTED.value: Step(StepIndex.NOT_STARTED.value, self),
            StepIndex.DNG_CONVERSION.value: Step(StepIndex.DNG_CONVERSION.value, self),
            StepIndex.COLOR_CORRECTION.value: Step(StepIndex.COLOR_CORRECTION.value, self),
            StepIndex.PHOTO_ALIGNMENT.value: Step(StepIndex.PHOTO_ALIGNMENT.value, self),
            StepIndex.MESH_CONSTRUCTION.value: Step(StepIndex.MESH_CONSTRUCTION.value, self),
            StepIndex.COMPLETED.value: Step(StepIndex.COMPLETED.value, self),
        }

    @property
    def task_data(self) -> dict:
        return self._task_data

    @property
    def task_location(self) -> Path:
        return Path(self._task_data[TASK_LOCATION_KEY])

    @property
    def cur_step(self) -> Step:
        """The current step."""
        return self._steps[self._cur_step_id]

    def sync_cur_step(self):
        """Scan task location and update current step ID value."""

        for step_id in sorted(STEP_METADATA.keys()):
            if self.task_location.joinpath(STEP_METADATA[step_id]['output_folder']).exists():
                self._cur_step_id += 1
            else:
                break
