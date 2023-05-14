'''
checks for existence of files in various capacities
'''

import subprocess
import sys
import os
import argparse
import json
import glob
import time

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from astropy.time import Time

from tools import current_time

def scan_objects(lc_path, fits_path):
    '''
    scans directory for lightcurves and compares against the list of directories in the fits folder
    
    Args:
        lc_path (str): path to lightcurve directory
        fits_path (str): path to fits directory
        
    Returns:
        new_objects (list): list of new objects found in lightcurve directory that are not in fits directory
        Note: this does not include the full path, just the object name
    
    To Do: May be better to rework so it uses gitpython to check for newly added objects rather than checking for folders
    '''
    objects = os.listdir(lc_path) ## list of objects in lightcurve directory
    object_names = [object.split('.')[0] for object in objects] ## list of object names in lightcurve directory
    
    fits_objects = os.listdir(fits_path) ## list of objects in fits directory (will be folders)
    
    new_objects_idx = [i for i, object in enumerate(object_names) if object not in fits_objects] ## indices of new objects
    new_objects = [objects[i] for i in new_objects_idx] ## list of new objects (including the extension)
    ## potential concern: could be a problem if there are multiple files for the same object (ie if the dat file has been made prior to this being run)
    if len(new_objects) > 0:
        print('[{}] New objects found: {}'.format(new_objects,current_time()))
        return new_objects
    else:
        print('[{}] No new objects found'.format(current_time()))
        return False
    

def check_fit_completion(objects, models, settings, elapsed_time):
    '''
    Checks for completion status of fits by looking for results.json files in the directory of the object
    
    Args:
        objects (list): path to directories of objects
        models (dict): dictionary of models and their settings
        settings (dict): settings dictionary from settings.json
    '''
    timeout = settings['timeout'] ## timeout in hours (default of 8 hours)
    object_completed_jobs = {object:[] for object in objects} ## dictionary of objects and their completed jobs
    object_uncompleted_jobs = {object:[] for object in objects} ## dictionary of objects and their uncompleted jobs
    for object in objects:
        for model, model_settings in models.items():
            object_directory = os.path.join(settings['fit_directory'], object, model)
            results_file = os.path.join(object_directory, '*_result.json')
            if os.path.exists(results_file):
                object_completed_jobs[object].append(model)
            elif not os.path.exists(results_file):
                object_uncompleted_jobs[object].append(model)
            else:
                continue
    num_completed = sum([len(object_completed_jobs[object]) for object in object_completed_jobs.keys()])
    num_fits = len(models.keys()) * len(objects)
    #print('[{}] {} of {} fits completed'.format(current_time(), num_completed, num_fits))
    if num_completed == num_fits:
        print('[{}] All fits completed'.format(current_time()))
        return True
    elif num_completed < num_fits:
        print('[{}] {} of {} fits remaining ({:.2f} hours elapsed)'.format(current_time(), num_fits - num_completed, num_fits, elapsed_time))
        return False
    elif elapsed_time > timeout:
        print('[{}] Timeout reached'.format(current_time()))
        return True