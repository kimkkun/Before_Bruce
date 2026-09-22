#!/usr/bin/python3
# Compatibility entry point; maintained source lives in the content Git repository.
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parents[2] / 'Kim.kkun_contents/methods/capcut-archive/archive_exports.py'), run_name='__main__')
