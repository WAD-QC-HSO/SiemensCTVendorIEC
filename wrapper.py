#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 11:40:27 2022

@author: erlean
"""

import os
import datetime
import pydicom as dcm
import analysis


def get_datetime(data, results):
    # Finding datetime of study

    # getting first image
    dc_path = os.path.abspath(data.series_filelist[0][0])
    dc = dcm.dcmread(dc_path, stop_before_pixels=True)
    date = str(dc[0x8, 0x20].value)
    time = str(dc[0x8, 0x30].value)[:6]
    try:
        dt = datetime.datetime.strptime(date + time, "%Y%m%d%H%M%S")
    except ValueError:
        dt = datetime.datetime.now()
    results.addDateTime("AquisitionDateTime", dt)


def analyse(data, results, config):
    analysis.analyse(data, results, config)


if __name__ == "__main__":
    from wad_qc.module import pyWADinput

    data, results, config = pyWADinput()

    for name, action in config["actions"].items():
        if name == "aqdatetime":
            get_datetime(data, results)
        if name == "analysis":
            analyse(data, results, config)

    results.write()
