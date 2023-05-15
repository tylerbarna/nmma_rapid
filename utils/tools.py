'''
Contains all miscellaneous functions that are used for the project.
'''
import os
import json
import time

import numpy as np
import pandas as pd
import bilby

from astropy.time import Time

from nmma.em.model import *


def current_time():
    '''
    returns current time in standardized format: YYYY-MM-DD HH:MM:SS
    '''
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

def parse_csv(infile, outdir=False):
    '''
    converts a .csv file to a .dat file in the format desired by NMMA
    
    Args:
        infile (str): path to .csv file
        outdir (str): path to directory to save .dat file to. If False, no file is saved.
    
    Returns:
        out_data (list): list of lists containing data in the format desired by NMMA
    '''
    in_data = np.genfromtxt(infile, dtype=None, delimiter=',', skip_header = 1, encoding = None)
    # Candidates are given keys that address a 2D array with
    # photometry data
    out_data = []
    for line in np.atleast_1d(in_data):
        #extract time and put in isot format
        time = Time(line[1], format='jd').isot
        filter = line[4]
        magnitude = line[2]
        error = line[3]
        if 99.0 == magnitude:
            magnitude = line[5]
            error = np.inf
        out_data.append([str(time), filter, str(magnitude), str(error)])
    if outdir:
        os.makedirs(outdir, exist_ok = True)
        # output the data
        # in the format desired by NMMA
        candname = infile.split('/')[-1].split('.')[0]
        out_file = open(outdir + candname + ".dat", 'w')
        for line in out_data:
            out_file.write(line[0] + " " + line[1] + " " + line[2] + " " + line[3] + "\n")
        out_file.close()

    return out_data

def get_filters(object):
    '''
    retrieve the filters detected for a given object
    
    Args:
        object (str): path to object lightcurve
    
    Returns:
        filters (list): list of filters detected for object
    '''
    data = pd.read_csv(object, sep=' ', header=None, names=['time','filter','mag','mag_err'])
    filters = data['filter'].unique()
    return filters


def read_results_json(jsonPath):
    '''
    reads in the results.json file from a completed fit
    
    Args:
        jsonPath (str): path to results.json file
        
    Returns:
        results (dict): dictionary of results
    '''
    
    with open(jsonPath) as f:
        results = json.load(f, object_hook=bilby.core.utils.decode_bilby_json)
    return results
    
    
def get_lightcurve_model(model):
    '''
    retreive the lightcurve model from nmma using the model-specific dictionary in settings.json
    
    Args:
        model (dict): dictionary of model, including job settings from settings.json (see fitting.generate_job for better idea of intended structure)
    
    Returns:
        lightcurve_model (class): lightcurve model from nmma
    '''
    model_function_name = model['model']
    model_function = eval(model_function_name)
    return model_function


def get_absolute_magnitude(distance, mag):
    '''
    converts apparent magnitude to absolute magnitude
    
    Args:
        distance (float,dict,list,np.ndarray): distance to object in Mpc
        mag (float): apparent magnitude of object
        
    Returns:
        absolute_magnitude (float): absolute magnitude of object
    '''
    absolute_magnitude = lambda mag, distance: mag + 5 * np.log10(distance * 1e6 / 10.0)
    if type(mag) == dict: ## in case of multiple filters
        return {filter: absolute_magnitude(mag[filter], distance) for filter in mag.keys()}
    elif type(mag) == list:
        return [absolute_magnitude(mag, distance) for mag in mag]
    elif type(mag) == np.ndarray:
        return np.array([absolute_magnitude(mag, distance) for mag in mag])
    else:
        return mag + 5 * np.log10(distance * 1e6 /10.0)