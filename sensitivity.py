#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 09:06:54 2020

@author: jh432
"""

import os
import subprocess
from typing import List, Tuple

import pandas as pd
import numpy as np
import uncertainpy as un
import chaospy as cp
import math

# global variables
workspace = '/home/jh432/eclipse-workspace/Battery_source_TDF_MCU/Release'
trace_file = "trace.dat"
model_path = "./Battery_source_TDF_MCU"

data = {'e0': 2.9,
        'A': 0.26422,
        'B': 1.67239511e-01,
        'K': 1.20800129e-04,
        'Q': 250.0,
        'Ri': 0.01
        }

designMatrix = [[0, 0, 0],
                [0, 0, 1],
                [0, 1, 0],
                [0, 1, 1],
                [1, 0, 0],
                [1, 0, 1],
                [1, 1, 0],
                [1, 1, 1]]

results = np.zeros(len(designMatrix))


def run_model(path, config_data):  # running the model with tracefile as return
    os.chdir(workspace)
    cmd = [path, trace_file, str(config_data['e0']), str(config_data['K']), str(config_data['A']), str(config_data['Ri']), str(config_data['B']), str(config_data['Q'])]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return trace_file


def read_tracefile(del_enable):  # reading tracefile
    trace_file_full_path = workspace + "/" + trace_file
    df = pd.read_csv(trace_file_full_path, delim_whitespace=True, skiprows=[1])
    df = df.iloc[::1000, :]  # observing interval
    df['%time'] = df['%time'] * (1 / 3600)
    if del_enable:
        os.remove(trace_file_full_path)
        print("File Removed!")
    return df


def extract_runtime(
        trace_df):  # extracting runtime from the tracefile (if runtime is not inside a certain threshold set to inf)
    runtime = trace_df.loc[trace_df['|Voltage-Booster-MCU|'] == 0]
    print(len(runtime))
    if len(runtime) > 0:
        return runtime['%time'].values[0]
    else:
        return math.inf


def return_effects(calc_v):  # calculating the effects
    total = [calc_v[0] - calc_v[1], calc_v[0] - calc_v[2], calc_v[0] - calc_v[4]]
    indiv = [calc_v[1] + calc_v[3] + calc_v[5] + calc_v[7], calc_v[2] + calc_v[3] + calc_v[6] + calc_v[7],
             calc_v[4] + calc_v[5] + calc_v[6] + calc_v[7]]
    inter = [total[0] - indiv[0], total[1] - indiv[1], total[2] - indiv[2]]
    return indiv, total, inter


def run_local_sensitivity_analysis():  # running the experiment design with two levels, three factors
    for i in range(2 ** 3):
        data['Ri'] = 0.01
        data['Q'] = 250.0
        data['K'] = 1.20800129e-04

        # 5% change
        if designMatrix[i][0] == 1:
            data['Ri'] += data['Ri'] * 0.05
        if designMatrix[i][1] == 1:
            data['Q'] += data['Q'] * 0.05
        if designMatrix[i][2] == 1:
            data['K'] += data['K'] * 0.05
        run_model(model_path, data)
        results[i] = extract_runtime(read_tracefile(True))
    print(results)
    print(return_effects(results))


run_local_sensitivity_analysis()  # starting the analysis
