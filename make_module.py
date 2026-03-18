# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 13:49:47 2022

@author: erlean
"""

import os
import shutil
from wad_qc.connection.exchange import make_factory_zip
import fix_line_endings


def create_outdir(name):
    parent = os.path.abspath(".")
    dirs = os.path.join(parent, "packages", name, "Config", "dcm_study", "meta")
    try:
        os.makedirs(dirs)
    except FileExistsError:
        pass


def generate():
    name = "ctqaiecsiemens"
    cdir = os.path.abspath(".")
    create_outdir(name)
    dest = os.path.join(cdir, "packages", name)

    shutil.copy("analysis.py", dest)
    shutil.copy("wrapper.py", dest)
    shutil.copy("ctseries.py", dest)
    shutil.copy("ctstudy.py", dest)
    shutil.copy("manifest.json", dest)

    if not os.path.exists(
        os.path.join(cdir, "Config", "dcm_study", "meta", "ctqaiecsiemens.json")
    ):
        shutil.copy(
            os.path.join(
                cdir, "Config", "dcm_study", "meta", "ctqaiecsiemens_auto.json"
            ),
            os.path.join(dest, "Config", "dcm_study", "meta", "ctqaiecsiemens.json"),
        )
    else:
        shutil.copy(
            os.path.join(cdir, "Config", "dcm_study", "meta", "ctqaiecsiemens.json"),
            os.path.join(dest, "Config", "dcm_study", "meta"),
        )
    shutil.copy(
        os.path.join(cdir, "Config", "dcm_study", "ctqaiecsiemens.json"),
        os.path.join(dest, "Config", "dcm_study", "ctqaiecsiemens.json"),
    )

    fix_line_endings.fix_all(dest)

    zip_dest = os.path.join(cdir, "packages", "modules_zip")
    try:
        os.makedirs(zip_dest)
    except FileExistsError:
        pass
    manifest_path = os.path.join(dest, "manifest.json")
    make_factory_zip(manifest_path, "zip_module", repo_info={}, outdir=zip_dest)


if __name__ == "__main__":

    generate()

    # manifest = os.path.abspath('manifest.json')
    # parentdir = os.path.abspath(os.path.join(manifest, '..', '..'))
    # dest = os.path.join(parentdir, 'CTQASiemens_packaged')
    # if not os.path.exists(dest):
    #     os.mkdir(dest)

    # fix_line_endings.fix_all()

    # make_factory_zip(manifest, 'zip_module', repo_info={}, outdir=dest)
