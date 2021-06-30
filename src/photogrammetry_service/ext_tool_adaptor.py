from pathlib import Path
import subprocess


def run_dng_conversion(input_file: Path, output_dir: Path, ext_tool_exe: Path):
    # TODO call adobe dng converter
    output_dir.mkdir(parents=True, exist_ok=True)
    sts = subprocess.Popen(
        f'"{ext_tool_exe.as_posix()}" -c -d "{output_dir.as_posix()}" "{input_file.as_posix()}"',
        shell=True,
    ).wait()


def run_photo_alignment(input_dir: Path, output_dir: Path, dummy_file: Path, ext_tool_exe: Path):
    # TODO: logic here
    #
    output_dir.mkdir(parents=True, exist_ok=True)
    f = open(dummy_file.as_posix(), 'w')


def run_mesh_construction(input_dir: Path, output_dir: Path, dummy_file: Path, ext_tool_exe: Path):
    # TODO: logic here
    #
    output_dir.mkdir(parents=True, exist_ok=True)
    f = open(dummy_file.as_posix(), 'w')
