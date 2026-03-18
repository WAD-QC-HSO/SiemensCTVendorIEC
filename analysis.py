# -*- coding: utf-8 -*-
"""
Created on Mon Apr 25 12:27:25 2022

@author: erlean
"""

import ctstudy


import numpy as np
import scipy
import scipy.ndimage
import scipy.interpolate
import skimage.filters


def circle_indices2D(shape, radii, center=None, inverse=False):
    X, Y = np.indices(shape)
    if center is None:
        c = list(s // 2 for s in shape)
    else:
        c = center
    if inverse:
        return (X - c[0]) ** 2 + (Y - c[1]) ** 2 > radii**2
    return (X - c[0]) ** 2 + (Y - c[1]) ** 2 <= radii**2


def consecutive_nonzero(array):
    ind = np.arange(array.size)
    splits = np.split(ind, ind[~array])
    split_ind = np.argmax(np.array([array[s].sum() for s in splits]))
    return np.array([i for i in ind[splits[split_ind]] if array[i]])


def analyseHomogeneity(series: list, result_object):
    results = dict()
    for serie in series:
        if not serie.valid:
            continue
        if serie.mode[0].find("Homogeneity") == -1:
            continue
        if serie.mode[-1].find("Water only") >= 0:
            continue
        label = "Homogeneity Tube{} {} {} {} ".format(
            serie.mode[4], serie.mode[3], serie.mode[1], serie.mode[2]
        )

        snitt = 1
        for ind, arr in enumerate(serie.getArrays()):
            px, _ = serie.getPixelSpacing(ind)
            rr = 75.0 / px
            r = 10.0 / px
            c = np.array(arr.shape) / 2
            lab = {
                "center": c,
                "north": c + np.array([0, rr]),
                "south": c + np.array([0, -rr]),
                "west": c + np.array([-rr, 0]),
                "east": c + np.array([rr, 0]),
            }
            homo_res = dict()

            for key, c in lab.items():
                idx = circle_indices2D(arr.shape, r, c)
                homo_res[key] = arr[idx].mean()
                results[label + "slice{} ".format(snitt) + key + " value"] = (
                    homo_res[key],
                    float,
                )
            for key, val in homo_res.items():
                if key != "center":
                    results[label + "slice {} ".format(snitt) + key + " difference"] = (
                        homo_res["center"] - val,
                        float,
                    )
            snitt += 1
        for key, (val, form) in results.items():
            if form == str:
                result_object.addString(key, val)
            else:
                result_object.addFloat(key, val)


def analyseContrast(series, result_object):
    results = dict()
    for serie in series:
        if not serie.valid:
            continue
        if serie.mode[0].find("Contrast") == -1:
            continue
        label = "Contrast Tube{} {} {} {} ".format(
            serie.mode[4], serie.mode[3], serie.mode[1], serie.mode[2]
        )

        snitt = 1
        for ind, arr in enumerate(serie.getArrays()):
            px, _ = serie.getPixelSpacing(ind)
            r = 30.0 / px
            idx = circle_indices2D(arr.shape, r)
            results[label + "slice {} {} value".format(snitt, serie.mode[5])] = (
                arr[idx].mean(),
                float,
            )
            snitt += 1
    for key, (val, form) in results.items():
        if form == str:
            result_object.addString(key, val)
        else:
            result_object.addFloat(key, val)


def interp(x0, x1, y0, y1, x):
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def mtfWorker(arr, px):
    dx = px[0]
    dist = 10.0 / dx
    center = np.array(arr.shape) / 2
    start, stop = int(np.round(center[0] - dist)), int(np.round(center[0] + dist))
    subarr = arr[start:stop, start:stop]

    background_idx = circle_indices2D(subarr.shape, int(dist / 4), inverse=True)
    background = subarr[background_idx].mean()
    subarr -= background
    subarr /= subarr.max()

    fft = np.abs(np.fft.fft2(subarr, (256, 256)))
    fft /= fft[0, 0]
    freq = np.fft.fftfreq(fft.shape[0], dx)
    X, Y = np.indices(fft.shape)
    F = np.sqrt(freq[X] ** 2 + freq[Y] ** 2)

    sort_ind = np.argsort(F.ravel())
    fft_lin = fft.ravel()[sort_ind]
    F_lin = F.ravel()[sort_ind]
    F_unique = np.unique(F_lin)
    t = F_unique[1:-5:4]
    s = scipy.interpolate.LSQUnivariateSpline(F_lin, fft_lin, t=t)

    i = 1
    mtf50 = None
    mtf10 = None
    while i < F_unique.size:
        x = np.array([F_unique[i - 1], F_unique[i]])
        y = s(x)

        if y[0] >= 0.5 and y[1] <= 0.5:
            mtf50 = interp(y[1], y[0], x[1], x[0], 0.5)
        elif y[0] >= 0.1 and y[1] <= 0.1:
            mtf10 = interp(y[1], y[0], x[1], x[0], 0.1)
        i += 1
    return mtf50 * 10, mtf10 * 10


def analyseMTF(series, result_object):
    results = dict()
    for serie in series:
        if not serie.valid:
            continue
        if serie.mode[0].find("MTF") == -1:
            continue
        kernel = "normal"
        if len(serie.mode) > 5:
            kernel = serie.mode[5]
        label = "MTF Tube{} {} {} {} {} ".format(
            serie.mode[4], serie.mode[3], serie.mode[1], serie.mode[2], kernel
        )

        snitt = 1
        for ind, arr in enumerate(serie.getArrays()):
            px, py = serie.getPixelSpacing(ind)
            mtf50, mtf10 = mtfWorker(arr, (px, py))
            if mtf50 is not None:
                results[label + "slice {} 50%".format(snitt)] = (
                    mtf50,
                    float,
                )
            if mtf10 is not None:
                results[label + "slice {} 10%".format(snitt)] = (
                    mtf10,
                    float,
                )
            snitt += 1
    for key, (val, form) in results.items():
        if form == str:
            result_object.addString(key, val)
        else:
            result_object.addFloat(key, val)


def analyseNoise(series, result_object):
    results = dict()
    for serie in series:
        if not serie.valid:
            continue
        if serie.mode[0].find("Noise") == -1:
            continue

        label = "Noise Tube{} {} {} {} ".format(
            serie.mode[4], serie.mode[3], serie.mode[1], serie.mode[2]
        )

        for ind, arr in enumerate(serie.getArrays()):
            key = label + "slice {}".format(ind + 1)
            if arr.min() < -500:
                if key not in results:
                    results[key] = list()
                results[key].append((arr, serie.getPixelSpacing(ind)[0]))

    result_sub = dict()
    for key, arrs in results.items():
        if len(arrs) > 1:
            a1 = arrs[0][0]
            a2 = arrs[1][0]
            px = arrs[0][1]
            idx = circle_indices2D(a1.shape, 40 / px)
            result_sub[key] = (a1 - a2)[idx].std()

    for key, val in result_sub.items():
        result_object.addFloat(key, val)


def analyseSlice(series, result_object):
    results = dict()
    for serie in series:
        if not serie.valid:
            continue
        if serie.mode[0].find("Slice") == -1:
            continue

        label = "Slice Tube{} {} {} {} {} ".format(
            serie.mode[4], serie.mode[3], serie.mode[1], serie.mode[2], serie.mode[5]
        )

        for ind, arr in enumerate(serie.getArrays()):
            key = label + "slice {}".format(ind + 1)
            spacing = serie.getPixelSpacing(ind)[0]

            ## Smooth image in direction normal to slice alu ramp
            gauss = skimage.filters.gaussian(arr, sigma=(4, 0), truncate=8.0)
            background = 100
            thres = background + (gauss.max() - background) / 2

            structure = scipy.ndimage.generate_binary_structure(2, 2)  # 8-connected
            labeled_array, num_features = scipy.ndimage.label(
                gauss > thres, structure=structure
            )

            slices = list()
            for l in range(1, num_features + 1):
                x = (labeled_array == l).max(axis=0)
                xx = len(consecutive_nonzero(x))
                slices.append(xx)

            results[key] = spacing * sum(slices) * np.tan(np.deg2rad(26)) / len(slices)

    for key, val in results.items():
        result_object.addFloat(key, val)


def writeMetadata(study, results):
    tags = {
        "Software version": (0x18, 0x1020),
        "Device serial number": (0x18, 0x1000),
        "Study description": (0x8, 0x1030),
        "Station name": (0x8, 0x1010),
    }
    for s in study.getSeries():
        for name, tag in tags.items():
            val = s.getDicomTag(tag)
            if val is not None:
                results.addString(name, str(val))
        return


def analyse(data, results, config):

    study = ctstudy.CTStudy(data)
    writeMetadata(study, results)

    series = study.getSeries()
    analyseSlice(series, results)
    analyseNoise(series, results)
    analyseMTF(series, results)
    analyseHomogeneity(series, results)
    analyseContrast(series, results)
