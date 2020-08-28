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


def run_and_return_time(Ri, Q):  # returning runtime of the simulation
    data['Ri'] = Ri
    data['Q'] = Q
    run_model(model_path, data)
    trace_file_full_path = workspace + "/" + trace_file
    runtime = extract_runtime(read_tracefile(trace_file_full_path, True))
    time = np.linspace(0, 200, 150)
    print(runtime)
    return time, runtime


def run_uncertainty_quantification():  # running uncertainty quantification using generalized polynomial chaos
    model = un.Model(run=run_and_return_time)
    Ri_dist = cp.TruncNormal(0.0049, 0.006, 0.005, 0.001)
    Q_dist = cp.TruncNormal(200, 235, 220, 20)
    parameters = {"Ri": Ri_dist, "Q": Q_dist}
    UQ = un.UncertaintyQuantification(model=model, parameters=parameters, CPUs=1)
    results = UQ.quantify(seed=10, pc_method="spectral")
    return results


run_uncertainty_quantification()  # starting the analysis
