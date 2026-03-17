# -*- coding: utf-8 -*-
import pydicom
import numpy as np
import skimage
import scipy


class CTSeries(object):

    _meta = {
        "RFOV": float,
        "KVP": float,
        "Kernel": str,
        "Slice thickness": float,
        "Filter": str,
        "Exposure": float,
        "CTDIvol": float,
        "InstanceNumber": int,
    }
    _tags = {
        "KVP": (0x18, 0x60),
        "RFOV": (0x18, 0x1100),
        "Kernel": (0x18, 0x1210),
        "Slice thickness": (0x18, 0x50),
        "Exposure": (0x18, 0x1152),
        "Filter": (0x18, 0x1160),
        "CTDIvol": (0x18, 0x9345),
        "InstanceNumber": (0x20, 0x30),
    }

    _mode_names_ = ["Mode", "kV", "Collimation", "Filter", "Tube", "Comment"]

    def __init__(self, dc_paths: list):
        self._dcs = dc_paths
        self._valid = False
        self._mode = list()
        if len(self._dcs) > 0:
            self._valid = self.findModes()

    def __len__(self):
        return len(self._dcs)

    @property
    def valid(self):
        return self._valid and len(self._mode) > 4

    @property
    def mode(self):
        return self._mode

    def findModes(self):
        image_comment_tag = (0x20, 0x4000)
        comment = None
        for d in self._dcs:
            dc = pydicom.dcmread(
                d,
                specific_tags=[
                    image_comment_tag,
                ],
            )
            if comment is None:
                comment = str(dc[image_comment_tag].value)
            else:
                c_cand = str(dc[image_comment_tag].value)
                if c_cand != comment:
                    return False
        if comment is None:
            return False
        comment = comment.strip()

        if comment.find("Noise") != -1:
            self._mode = comment.split("; ")
            last = self._mode.pop(-1)
            self._mode += last.split(",")
            return True
        elif comment.find("Contrast") != -1:
            self._mode = comment.split("; ")
            first = self._mode[0].split(" ")
            self._mode[0] = first[1]
            self._mode.insert(0, first[0])
            first = self._mode[-1].split(" ")
            self._mode[-1] = first[0]
            self._mode.append(first[1])
            return True
        elif comment.find("Homogeneity") != -1:
            self._mode = comment.split("; ")
            return True
        elif comment.find("MTF") != -1:
            self._mode = comment.split("; ")
            return True
        elif comment.find("Slice") != -1:
            self._mode = comment.split("; ")
            first = self._mode[0].split(" ")
            self._mode[0] = first[1]
            self._mode.insert(0, first[0])
            return True
        return False

    def getMetaData(self, index: int = -1):
        if not self._valid:
            return None
        meta = dict()
        if index < 0:
            index = 0
        if index >= len(self):
            return None

        dc = pydicom.dcmread(self._dcs[index], specific_tags=list(self._tags.values()))
        for key, tag in self._tags.items():
            meta[key] = self._meta[key](dc[tag].value)
        return meta

    def getPixelSpacing(self, index):
        if index < 0 or index >= len(self):
            raise IndexError("Image index aout of bounds")
        px = self.getDicomTag((0x28, 0x30))
        if px is None:
            raise KeyError("Dicom tag pixel_spacing not in image")
        return float(px[0]), float(px[1])

    def getkVp(self):
        kv = self.getDicomTag((0x18, 0x60))
        if kv is None:
            raise KeyError("Dicom tag kVp not in image")
        return int(kv)

    def getDicomTag(self, tag, index=0):
        val = None
        if index >= len(self):
            return val
        try:
            dc = pydicom.dcmread(self._dcs[index], specific_tags=[tag])
            val = dc[tag].value
        except KeyError:
            return None
        return val

    def getArrays(self):
        if not self._valid:
            return None
        ds = list([pydicom.dcmread(f) for f in self._dcs])
        ds.sort(key=lambda x: int(x[(0x20, 0x13)].value))
        arrs = [self.getArray(d) for d in ds]
        return list(arrs)

    @staticmethod
    def getArray(dc):
        lut = pydicom.pixel_data_handlers.apply_modality_lut
        return lut(dc.pixel_array.astype(np.float64), dc)
