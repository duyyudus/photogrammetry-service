from pathlib import Path
import subprocess

PREPARE_RC_MARKER = 'project.rcproj'
MESH_CONSTRUCTION_MARKER = 'output.fbx'


def run_dng_conversion(input_file: Path, output_dir: Path, ext_tool_exe: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = f'"{ext_tool_exe}" -c -d "{output_dir}" "{input_file}"'
    print(cmd)
    sts = subprocess.Popen(
        cmd,
        shell=True,
    ).wait()
    return sts


def run_prepare_rc(input_dir: Path, output_dir: Path, ext_tool_exe: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    rc_project = output_dir.joinpath(PREPARE_RC_MARKER)

    command = '"{}" -newScene -addFolder "{}" -align \
        -setReconstructionRegionAuto -save "{}" -quit'.format(
        ext_tool_exe, input_dir, rc_project
    )

    sts = subprocess.Popen(
        command,
        shell=True,
    ).wait()

    return sts


def run_mesh_construction(input_dir: Path, output_dir: Path, ext_tool_exe: Path, rc_setting: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    rc_project = input_dir.joinpath(PREPARE_RC_MARKER)
    output_mesh = output_dir.joinpath(MESH_CONSTRUCTION_MARKER)

    command = '"{}" -load "{}" -calculateNormalModel -unwrap "{}" -calculateTexture \
    -exportSelectedModel "{}" "{}" -exportLod "{}" "{}" -save "{}" -quit'.format(
        ext_tool_exe,
        rc_project,
        rc_setting.joinpath("RC_UV_16K_Optimal.xml"),
        output_mesh,
        rc_setting.joinpath("RC_ExportFBX_VC_noTEX.xml"),
        output_dir.joinpath("RC_LOD.obj"),
        rc_setting.joinpath("RC_ExportLOD_TEX_noVC.xml"),
        rc_project,
    )

    sts = subprocess.Popen(
        command,
        shell=True,
    ).wait()

    return sts
