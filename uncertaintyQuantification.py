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


def run_and_return_time(Ri, Q):  # returning runtime of the simulation
    run_model(gl_tracefile, gl_e0, gl_K, gl_A, Ri, gl_B, Q)
    path_trace = '/home/jh432/eclipse-workspace/Battery_source_TDF_MCU/Release' + "/" + gl_tracefile
    runtime = extract_runtime(read_tracefile(path_trace, True))
    time = np.linspace(0, 200, 150)
    print(runtime)
    return time, runtime


def run_uncertainty_quantification(): # running uncertainty quantification using generalized polynomial chaos
    model = un.Model(run=run_and_return_time)
    Ri_dist = cp.TruncNormal(0.0049, 0.006, 0.005, 0.001)
    Q_dist = cp.TruncNormal(200, 235, 220, 20)
    parameters = {"Ri": Ri_dist, "Q": Q_dist}
    UQ = un.UncertaintyQuantification(model=model, parameters=parameters, CPUs=1)
    data = UQ.quantify(seed=10, pc_method="spectral")
    return data


run_uncertainty_quantification()  # starting the analysis
