#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 09:06:54 2020

@author: jh432
"""

import os
import subprocess
import pandas as pd
import numpy as np
import uncertainpy as un
import chaospy as cp
import math

# global variables
gl_tracefile = "trace.dat"
gl_e0 = 2.9
gl_A = 0.26422
gl_B = 1.67239511e-01
gl_K = 1.20800129e-04
gl_Q = 250.0
gl_Ri = 0.01

vect = [[0, 0, 0],
        [0, 0, 1],
        [0, 1, 0],
        [0, 1, 1],
        [1, 0, 0],
        [1, 0, 1],
        [1, 1, 0],
        [1, 1, 1]]
change = [0.05]  # 5% change
calc = np.zeros(len(vect * len(change)))


def run_model(tracefile, e0, K, A, Ri, B, Q):  # running the model with tracefile as return
    os.chdir('/home/jh432/eclipse-workspace/Battery_source_TDF_MCU/Release')
    cmd = ["./Battery_source_TDF_MCU", tracefile, str(e0), str(K), str(A), str(Ri), str(B), str(Q)]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return tracefile


def read_tracefile(tracefile_full_path, del_enable):  # reading tracefile
    df = pd.read_csv(tracefile_full_path, delim_whitespace=True, skiprows=[1])
    df = df.iloc[::1000, :]  # observing interval
    df['%time'] = df['%time'] * (1 / 3600)
    if del_enable:
        os.remove(tracefile_full_path)
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
    for j in range(len(change)):
        for i in range(2 ** 3):
            e0 = gl_e0
            K = gl_K
            A = gl_A
            Ri = gl_Ri
            B = gl_B
            Q = gl_Q

            print(vect[i], " ", change[j])
            if vect[i][0] == 1:
                Ri = Ri + (Ri * change[j])
            if vect[i][1] == 1:
                Q = Q + (Q * change[j])
            if vect[i][2] == 1:
                K = K + (K * change[j])
            run_model(gl_tracefile, e0, K, A, Ri, B, Q)
            path_trace = '/home/jh432/eclipse-workspace/Battery_source_TDF_MCU/Release' + "/" + gl_tracefile
            calc[i + j * len(vect)] = extract_runtime(read_tracefile(path_trace, True))
    print(calc)
    print(return_effects(calc))


run_local_sensitivity_analysis()  # starting the analysis
