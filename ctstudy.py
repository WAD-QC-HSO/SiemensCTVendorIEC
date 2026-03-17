# -*- coding: utf-8 -*-

import pydicom
import ctseries


class CTStudy(object):
    def __init__(self, data):

        self._series = list()
        ct_sop_value = "1.2.840.10008.5.1.4.1.1.2"
        ct_sop_tag = (0x8, 0x16)
        ct_imtype_tag = (0x8, 0x8)
        seruid_tag = (0x20, 0xE)
        comment_tag = (0x20, 0x4000)

        specific_tags = [ct_sop_tag, ct_imtype_tag, seruid_tag, comment_tag]

        series = dict()

        for ser in data.series_filelist:
            for im in ser:
                try:
                    dc = pydicom.dcmread(im, specific_tags=specific_tags)
                except:
                    pass
                else:
                    if dc[ct_sop_tag].value == ct_sop_value:  # "CT Image Storage":
                        imtype = dc[ct_imtype_tag].value
                        if (
                            imtype[0] == "ORIGINAL"
                            and imtype[1] == "PRIMARY"
                            and imtype[2] == "AXIAL"
                        ):
                            ser_uid = dc[seruid_tag].value
                            if ser_uid not in series:
                                series[ser_uid] = list()
                            series[ser_uid].append(im)

        self._series = list([ctseries.CTSeries(v) for v in series.values()])

    def writeStudyMetaData(self, result):
        float_res = dict()
        str_res = dict()

        for key, dtype in self._meta.items():
            tag = self._tags[key]
            try:
                value = dtype(self._series[0].getDicomValue(tag))
            except Exception as e:
                raise KeyError("Could not find dicom tag {} for study".format(tag))
                return
            if dtype == str:
                str_res[key] = value
            elif dtype == float:
                float_res[key] = value

        for series in self._series:
            tube = series.tubeSystem()
            atype = series.analysisType()
            for key, dtype in self._tube_meta.items():
                name = key + " Tube " + tube
                if (name not in float_res) and (name not in str_res):
                    tag = self._tags[key]
                    try:
                        value = dtype(series.getDicomValue(tag))
                    except Exception as e:
                        raise KeyError(
                            "Could not find dicom tag {} for study".format(tag)
                        )

                    if dtype == str:
                        str_res[name] = value
                    elif dtype == float:
                        float_res[name] = value
            for key, dtype in self._type_meta.items():
                name = key + " " + atype
                if (name not in float_res) and (name not in str_res):
                    tag = self._tags[key]
                    try:
                        value = dtype(series.getDicomValue(tag))
                    except Exception as e:
                        raise KeyError(
                            "Could not find dicom tag {} for study".format(tag)
                        )
                    if dtype == str:
                        str_res[name] = (
                            value.replace("[", "")
                            .replace("]", "")
                            .replace("'", "")
                            .replace(",", "")
                        )
                    elif dtype == float:
                        float_res[name] = value

        for key, value in float_res.items():
            result.addFloat(key, value)
        for key, value in str_res.items():
            result.addString(key, value)

    def getSeries(self):
        return self._series
