# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 14:54:37 2022

@author: erlean
"""
import pydicom
import os
import json

import wrapper


class Result(object):
    def __init__(self):
        self.data = dict()

    def addFloat(self, name, val):
        self.data[name] = (val, "float")
        print("Added float result {}: {}".format(name, val))

    def addBool(self, name, val):
        self.data[name] = (val, "bool")
        print("Added bool result {}: {}".format(name, val))

    def addString(self, name, val):
        self.data[name] = (val, "string")
        print("Added string result {}: {}".format(name, val))

    def addDateTime(self, name, val):
        self.data[name] = (val, "datetime")
        print("Added datetime result {}: {}".format(name, val))

    def getConfig(self):
        d = dict()
        d["comments"] = {
            "author": "Erlend Andersen",
            "version": "20220422",
            "description": "CT analysis of Siemens vendor phantom from Siemens IEC images",
        }
        d["metaformat"] = "20180910"

        results = dict()
        for name, (val, typ) in self.data.items():
            r = {
                "display_name": name,
                "display_level": 2,
                "description": name,
                "constraint_is_active": False,
                "units": "",
            }
            if typ == "float":
                r["decimals"] = 2
            if typ == "datetime":
                r["constraint_period"] = 3
            results[name] = r

        d["results"] = results
        return json.dumps(d)


class Data(object):
    def __init__(self, image_folder, collapse_all_series=False):

        self.series_filelist = list()
        series = dict()
        for f in self.find_all_files(image_folder):
            try:
                dc = pydicom.dcmread(f, stop_before_pixels=True)
            except:
                pass
            else:
                try:
                    uid = dc[0x20, 0xE].value
                except:
                    pass
                else:
                    if uid not in series:
                        series[uid] = list()
                    series[uid].append(f)

        if collapse_all_series:
            self.series_filelist = [[]]
            for v in series.values():
                self.series_filelist[0] += v
        else:
            for v in series.values():
                self.series_filelist.append(v)

    def find_all_files(self, path):
        if os.path.isdir(path):
            for dirname, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    yield os.path.normpath(os.path.join(dirname, filename))

        elif os.path.isfile(path):
            yield os.path.normpath(path)


if __name__ == "__main__":

    writeConfig = True

    testdata = r"C:\Users\ander\source\SiemensCTVendorIEC\SiemensCTVendorIEC\testbilder"

    results = Result()
    data = Data(testdata, False)
    config = {"actions": {"aqdatetime": [], "analysis": []}}

    wrapper.get_datetime(data, results)
    wrapper.analyse(data, results, config)

    conf = results.getConfig()
    if writeConfig:
        with open("./Config/dcm_study/meta/ctqasiemens_auto.json", "w") as f:
            f.write(conf)
