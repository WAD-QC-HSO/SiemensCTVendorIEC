# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 08:58:10 2021

@author: ander
"""

import os

def fix_all(path_to_fix):
    for path, folders, files in os.walk(path_to_fix):
        for fil in files:
            filepath = os.path.join(path, fil)
            ext = os.path.splitext(filepath)[-1].lower()
            if ext in ['.py', '.json']:
                fix_file(filepath)
                print("Converted line ending for file {}".format(filepath))

def fix_file(path):
    with open(path, 'rb+') as f:
        content = f.read()
        f.seek(0)
        f.write(content.replace(b'\r', b''))
        f.truncate()




if __name__ == '__main__':
    fix_all()
