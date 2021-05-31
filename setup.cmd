set PY_DIR=C:\Python38

"%PY_DIR%/python" -m venv venv
"venv/Scripts/pip" install -e .[dev]
"venv/Scripts/pip" install PythonMagick-0.9.19-cp38-cp38-win_amd64.whl