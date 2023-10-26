# -*- coding:utf-8 -*-
import subprocess
import sys


def convert(in_path, out_path):
    cmd = f'ffmpeg -re -i "{in_path}" -acodec copy -vcodec copy -f mp4 "{out_path}"'
    print(f'cmd {cmd}')
    p = subprocess.Popen(cmd,
                         shell=True,
                         stdout=sys.stdout,
                         stderr=sys.stderr,
                         )
    p.wait()
    print(f'ret={p.returncode}')
    return p.returncode
